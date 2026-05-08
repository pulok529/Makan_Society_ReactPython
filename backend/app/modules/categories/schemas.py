from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str
    code: str | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str
    code: str | None = None
    is_active: bool = True


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None
    is_active: bool
