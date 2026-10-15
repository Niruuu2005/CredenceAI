"""
Identity & Access Management module for CredenceAI 2.0.
Provides AuthContext, multi-tenant workspace scoping, and RBAC enforcement.
"""

from app.identity.auth_context import AuthContext, WorkspaceRole, Permission, ROLE_PERMISSIONS
from app.identity.dependencies import get_auth_context, require_permission

__all__ = [
    "AuthContext",
    "WorkspaceRole",
    "Permission",
    "ROLE_PERMISSIONS",
    "get_auth_context",
    "require_permission",
]
