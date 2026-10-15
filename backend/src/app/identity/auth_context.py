"""
AuthContext and RBAC definitions for CredenceAI 2.0.
Implements FR-001, IAM-01, IAM-02, IAM-03.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Optional
from fastapi import HTTPException, status


class WorkspaceRole(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class Permission(str, Enum):
    # Research & Run permissions
    READ_RESEARCH = "research:read"
    CREATE_RESEARCH = "research:create"
    CANCEL_RESEARCH = "research:cancel"

    # Evidence & Review permissions
    REVIEW_EVIDENCE = "evidence:review"

    # Report & Export permissions
    EXPORT_REPORT = "report:export"

    # Monitoring & Collections
    MANAGE_MONITORS = "monitors:manage"
    MANAGE_COLLECTIONS = "collections:manage"

    # Administration & Governance
    MANAGE_WORKSPACE = "workspace:manage"


ROLE_PERMISSIONS: dict[WorkspaceRole, Set[Permission]] = {
    WorkspaceRole.ADMIN: {
        Permission.READ_RESEARCH,
        Permission.CREATE_RESEARCH,
        Permission.CANCEL_RESEARCH,
        Permission.REVIEW_EVIDENCE,
        Permission.EXPORT_REPORT,
        Permission.MANAGE_MONITORS,
        Permission.MANAGE_COLLECTIONS,
        Permission.MANAGE_WORKSPACE,
    },
    WorkspaceRole.RESEARCHER: {
        Permission.READ_RESEARCH,
        Permission.CREATE_RESEARCH,
        Permission.CANCEL_RESEARCH,
        Permission.EXPORT_REPORT,
        Permission.MANAGE_MONITORS,
        Permission.MANAGE_COLLECTIONS,
    },
    WorkspaceRole.REVIEWER: {
        Permission.READ_RESEARCH,
        Permission.REVIEW_EVIDENCE,
        Permission.EXPORT_REPORT,
    },
    WorkspaceRole.VIEWER: {
        Permission.READ_RESEARCH,
    },
}


@dataclass(frozen=True)
class AuthContext:
    """
    Immutable authorization context derived on the server.
    All private API endpoints, database queries, indexes, caches,
    and storage lookups MUST be scoped by this context.
    """
    user_id: str
    tenant_id: str
    workspace_id: str
    role: WorkspaceRole
    permissions: Set[Permission] = field(default_factory=set)
    auth_method: str = "jwt"  # "jwt", "api_key", "system"
    api_key_id: Optional[int] = None

    def has_permission(self, permission: Permission) -> bool:
        """Check if current context has a specific permission."""
        return permission in self.permissions

    def require_permission(self, permission: Permission) -> None:
        """Raise 403 Forbidden if permission is missing."""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: action requires '{permission.value}' permission in workspace '{self.workspace_id}'.",
            )
