from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_auth_service, get_current_permissions, get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    BootstrapAdminRequest,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserProfile,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap-admin", response_model=UserProfile)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    user = service.bootstrap_admin(
        username=payload.username,
        login_name=payload.login_name,
        email=payload.email,
        password=payload.password,
    )
    return UserProfile.model_validate(
        {
            "id": user.id,
            "username": user.username,
            "login_name": user.login_name,
            "email": user.email,
            "is_active": user.is_active,
            "permissions": ["admin:manage", "billing:manage", "members:manage", "reports:view"],
        }
    )


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    return service.login(login_name=payload.login_name, password=payload.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    return service.refresh(refresh_token=payload.refresh_token)


@router.get("/me", response_model=UserProfile)
def me(
    current_user: User = Depends(get_current_user),
    permissions: list[str] = Depends(get_current_permissions),
) -> UserProfile:
    return UserProfile.model_validate(
        {
            "id": current_user.id,
            "username": current_user.username,
            "login_name": current_user.login_name,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "permissions": permissions,
        }
    )
