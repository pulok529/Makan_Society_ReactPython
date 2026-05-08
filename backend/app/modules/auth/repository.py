from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import Permission, RefreshToken, Role, RolePermission, User, UserRole


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_login_name(self, login_name: str) -> User | None:
        stmt = select(User).where(User.login_name == login_name)
        return self.db.scalar(stmt)

    def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.scalar(stmt)

    def add_refresh_token(self, refresh_token: RefreshToken) -> None:
        self.db.add(refresh_token)

    def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = refresh_token.revoked_at

    def get_user_permissions(self, user_id: int) -> list[str]:
        stmt = (
            select(Permission.resource, Permission.action)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return [f"{resource}:{action}" for resource, action in self.db.execute(stmt).all()]

    def user_count(self) -> int:
        return len(self.db.execute(select(User.id)).all())
