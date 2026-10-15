"""
FastAPI dependency injection for AuthContext and RBAC enforcement.
Implements FR-001, IAM-01, IAM-02, IAM-03.
"""

from typing import Optional, Callable
import uuid
import logging
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Tenant, Workspace, Membership, ApiKey
from app.services.security import _user_from_jwt
from app.services.api_key_service import validate_api_key
from app.identity.auth_context import (
    AuthContext,
    WorkspaceRole,
    Permission,
    ROLE_PERMISSIONS,
)

logger = logging.getLogger(__name__)
bearer_security = HTTPBearer(auto_error=False)


def get_or_create_default_workspace(db: Session, user: User) -> tuple[Workspace, Membership]:
    """
    Ensure a user always has at least one default workspace.
    Guarantees seamless backward compatibility for existing accounts.
    """
    existing_mem = (
        db.query(Membership)
        .filter(Membership.user_id == user.id)
        .first()
    )
    if existing_mem:
        workspace = db.query(Workspace).filter(Workspace.id == existing_mem.workspace_id).first()
        if workspace:
            return workspace, existing_mem

    # Create personal tenant and workspace
    tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
    tenant_name = f"{user.name or user.email}'s Organization"
    tenant = Tenant(id=tenant_id, name=tenant_name)
    db.add(tenant)
    db.flush()

    ws_id = f"ws_{uuid.uuid4().hex[:12]}"
    ws_name = f"{user.name or user.email}'s Workspace"
    workspace = Workspace(
        id=ws_id,
        tenant_id=tenant.id,
        name=ws_name,
        description="Default personal workspace",
    )
    db.add(workspace)
    db.flush()

    membership_id = f"mem_{uuid.uuid4().hex[:12]}"
    membership = Membership(
        id=membership_id,
        user_id=user.id,
        workspace_id=workspace.id,
        role=WorkspaceRole.ADMIN.value,
    )
    db.add(membership)
    db.commit()
    db.refresh(workspace)
    db.refresh(membership)
    return workspace, membership


def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AuthContext:
    """
    Primary authorization dependency.
    Extracts authentication credentials, verifies workspace membership,
    and returns a sealed, immutable AuthContext.
    
    CRITICAL SECURITY INVARIANT:
    Workspace is derived strictly from verified credentials + verified membership.
    Any attempt to target an un-joined workspace via X-Workspace-Id raises 403 Forbidden.
    """
    user: Optional[User] = None
    auth_method = "jwt"
    bound_api_key: Optional[ApiKey] = None

    # 1. Try Bearer JWT or Bearer API Key
    if credentials and credentials.credentials:
        user = _user_from_jwt(credentials.credentials, db)
        if not user:
            # Check if Bearer token is an API key
            validated = validate_api_key(db, credentials.credentials)
            if validated:
                bound_api_key = validated
                auth_method = "api_key"
                if bound_api_key.user_id:
                    user = db.query(User).filter(User.id == bound_api_key.user_id).first()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Bearer token or API key.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # 2. Try X-API-Key header if not authenticated yet
    if not user and x_api_key:
        validated = validate_api_key(db, x_api_key)
        if not validated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API key.",
            )
        bound_api_key = validated
        auth_method = "api_key"
        if bound_api_key.user_id:
            user = db.query(User).filter(User.id == bound_api_key.user_id).first()

    # 3. Fallback to request.state if set by middleware
    if not user:
        api_key_user_id = getattr(request.state, "api_key_user_id", None)
        if api_key_user_id:
            user = db.query(User).filter(User.id == api_key_user_id).first()
            auth_method = "api_key"

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token or X-API-Key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended.",
        )

    # 4. Resolve Target Workspace
    # If API key is hard-bound to a workspace, it cannot be overridden
    target_workspace_id = x_workspace_id
    if bound_api_key and bound_api_key.workspace_id:
        if target_workspace_id and target_workspace_id != bound_api_key.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key is restricted to workspace '{bound_api_key.workspace_id}'. Cross-workspace access denied.",
            )
        target_workspace_id = bound_api_key.workspace_id

    # 5. Verify Workspace Membership
    membership: Optional[Membership] = None
    if target_workspace_id:
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == target_workspace_id,
            )
            .first()
        )
        if not membership:
            # Cross-workspace probe blocked!
            logger.warning(
                f"Security event: User '{user.id}' attempted unauthorized access to workspace '{target_workspace_id}'."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You are not a member of workspace '{target_workspace_id}'.",
            )
        workspace = db.query(Workspace).filter(Workspace.id == target_workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace '{target_workspace_id}' not found.",
            )
    else:
        # Default workspace resolution
        workspace, membership = get_or_create_default_workspace(db, user)

    # 6. Parse Role and Calculate Permissions
    try:
        role = WorkspaceRole(membership.role)
    except ValueError:
        role = WorkspaceRole.VIEWER

    permissions = set(ROLE_PERMISSIONS.get(role, set()))

    return AuthContext(
        user_id=user.id,
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        role=role,
        permissions=permissions,
        auth_method=auth_method,
        api_key_id=bound_api_key.id if bound_api_key else None,
    )


def require_permission(permission: Permission) -> Callable:
    """
    Dependency factory to enforce required permission on a route.
    Usage:
        @router.post("/research-runs")
        def create_run(auth: AuthContext = Depends(require_permission(Permission.CREATE_RESEARCH))):
            ...
    """
    def _dependency(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        auth.require_permission(permission)
        return auth

    return _dependency


def get_auth_context_allow_guest(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AuthContext:
    """
    Authorization dependency that permits unauthenticated guests to explore research.
    If valid credentials are provided, authenticates to the user's personal/org workspace.
    If no credentials are provided, falls back to an isolated guest workspace seamlessly.
    """
    try:
        return get_auth_context(request, credentials, x_workspace_id, x_api_key, db)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            guest_user = db.query(User).filter(User.id == "user_public_guest").first()
            if not guest_user:
                guest_user = User(
                    id="user_public_guest",
                    email="guest@credenceai.local",
                    name="Public Guest Researcher",
                    role="member",
                    account_status="active",
                )
                db.add(guest_user)
                db.flush()
            workspace, membership = get_or_create_default_workspace(db, guest_user)
            return AuthContext(
                user_id=guest_user.id,
                tenant_id=workspace.tenant_id,
                workspace_id=workspace.id,
                role=WorkspaceRole.ADMIN,
                permissions=set(ROLE_PERMISSIONS[WorkspaceRole.ADMIN]),
                auth_method="guest",
                api_key_id=None,
            )
        raise
