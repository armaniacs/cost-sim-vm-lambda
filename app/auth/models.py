"""
Authentication models for enterprise security
"""
import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.declarative import declarative_base

from app.models.database import Base


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for this user"""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return list(permissions)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'roles': [role.name for role in self.roles],
            'permissions': self.get_permissions()
        }


class Role(Base):
    """Role model for role-based access control"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
    
    def __repr__(self):
        return f"<Role(name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """Convert role to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'permissions': [perm.name for perm in self.permissions]
        }


class Permission(Base):
    """Permission model for fine-grained access control"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    resource = Column(String(100), nullable=False)  # e.g., 'calculator', 'pricing', 'analytics'
    action = Column(String(50), nullable=False)     # e.g., 'read', 'write', 'delete', 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self):
        return f"<Permission(name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """Convert permission to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RefreshToken(Base):
    """Refresh token model for token management"""
    __tablename__ = 'refresh_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """Check if refresh token is expired"""
        return datetime.datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if refresh token is valid"""
        return not self.is_revoked and not self.is_expired()


class UserRole(Base):
    """User role assignment model with additional metadata"""
    __tablename__ = 'user_role_assignments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.id'))
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)  # Optional expiration for temporary roles
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    role: Mapped["Role"] = relationship("Role")
    assigner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    def is_expired(self) -> bool:
        """Check if role assignment is expired"""
        if not self.expires_at:
            return False
        return datetime.datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if role assignment is valid"""
        return self.is_active and not self.is_expired()


# Default roles and permissions for the system
DEFAULT_PERMISSIONS = [
    # Calculator permissions
    ("calculator:read", "Read calculator data", "calculator", "read"),
    ("calculator:write", "Write calculator data", "calculator", "write"),
    ("calculator:admin", "Admin calculator operations", "calculator", "admin"),
    
    # Pricing permissions
    ("pricing:read", "Read pricing data", "pricing", "read"),
    ("pricing:write", "Write pricing data", "pricing", "write"),
    ("pricing:admin", "Admin pricing operations", "pricing", "admin"),
    
    # Analytics permissions
    ("analytics:read", "Read analytics data", "analytics", "read"),
    ("analytics:write", "Write analytics data", "analytics", "write"),
    ("analytics:admin", "Admin analytics operations", "analytics", "admin"),
    
    # Regions permissions
    ("regions:read", "Read regions data", "regions", "read"),
    ("regions:write", "Write regions data", "regions", "write"),
    ("regions:admin", "Admin regions operations", "regions", "admin"),
    
    # ML permissions
    ("ml:read", "Read ML data", "ml", "read"),
    ("ml:write", "Write ML data", "ml", "write"),
    ("ml:admin", "Admin ML operations", "ml", "admin"),
    
    # Reports permissions
    ("reports:read", "Read reports", "reports", "read"),
    ("reports:write", "Generate reports", "reports", "write"),
    ("reports:admin", "Admin reports operations", "reports", "admin"),
    
    # User management permissions
    ("users:read", "Read user data", "users", "read"),
    ("users:write", "Write user data", "users", "write"),
    ("users:admin", "Admin user operations", "users", "admin"),
    
    # System permissions
    ("system:read", "Read system data", "system", "read"),
    ("system:admin", "Admin system operations", "system", "admin"),
]

DEFAULT_ROLES = [
    ("admin", "System administrator with full access", [
        "calculator:admin", "pricing:admin", "analytics:admin", "regions:admin",
        "ml:admin", "reports:admin", "users:admin", "system:admin"
    ]),
    ("manager", "Manager with read/write access to most resources", [
        "calculator:write", "pricing:write", "analytics:write", "regions:write",
        "ml:write", "reports:write", "users:read", "system:read"
    ]),
    ("analyst", "Analyst with read/write access to analytics and reports", [
        "calculator:read", "pricing:read", "analytics:write", "regions:read",
        "ml:read", "reports:write", "system:read"
    ]),
    ("viewer", "Read-only access to most resources", [
        "calculator:read", "pricing:read", "analytics:read", "regions:read",
        "ml:read", "reports:read", "system:read"
    ]),
    ("api_user", "API access for external integrations", [
        "calculator:read", "pricing:read", "analytics:read", "regions:read"
    ])
]