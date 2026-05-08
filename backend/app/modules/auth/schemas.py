from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    login_name: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    login_name: str
    email: str | None
    is_active: bool
    permissions: list[str]


class BootstrapAdminRequest(BaseModel):
    username: str
    login_name: str
    email: str | None = None
    password: str
