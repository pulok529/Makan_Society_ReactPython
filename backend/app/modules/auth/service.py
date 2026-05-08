from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.models import Permission, RefreshToken, Role, RolePermission, User, UserRole
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import TokenPair


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuthRepository(db)

    def bootstrap_admin(
        self,
        *,
        username: str,
        login_name: str,
        email: str | None,
        password: str,
    ) -> User:
        if self.repository.user_count() > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Users already exist")

        user = User(
            username=username,
            login_name=login_name,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
        )
        role = Role(name="admin", description="System administrator")
        permissions = [
            Permission(resource="members", action="manage", description="Manage members"),
            Permission(resource="billing", action="manage", description="Manage billing"),
            Permission(resource="reports", action="view", description="View reports"),
            Permission(resource="admin", action="manage", description="Manage admin settings"),
        ]

        self.db.add(user)
        self.db.add(role)
        for permission in permissions:
            self.db.add(permission)
        self.db.flush()

        self.db.add(UserRole(user_id=user.id, role_id=role.id))
        for permission in permissions:
            self.db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, *, login_name: str, password: str) -> TokenPair:
        user = self.repository.get_user_by_login_name(login_name)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials",
            )

        access_token = create_access_token(str(user.id))
        refresh_token_value, expires_at = create_refresh_token(str(user.id))
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_value),
            expires_at=expires_at,
        )
        self.repository.add_refresh_token(refresh_token)
        self.db.commit()

        return TokenPair(access_token=access_token, refresh_token=refresh_token_value)

    def refresh(self, *, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        stored_token = self.repository.get_refresh_token(hash_token(refresh_token))
        if stored_token is None or stored_token.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognized")
        if stored_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        access_token = create_access_token(payload["sub"])
        next_refresh_token, expires_at = create_refresh_token(payload["sub"])
        stored_token.revoked_at = datetime.now(UTC)
        self.db.add(
            RefreshToken(
                user_id=stored_token.user_id,
                token_hash=hash_token(next_refresh_token),
                expires_at=expires_at,
            )
        )
        self.db.commit()
        return TokenPair(access_token=access_token, refresh_token=next_refresh_token)

    def get_current_user(self, token: str) -> User:
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

        user = self.repository.get_user_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")
        return user
