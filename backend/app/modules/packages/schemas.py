from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PackageCreate(BaseModel):
    category_id: int
    name: str
    package_type: str | None = None
    default_price: float
    is_active: bool = True


class PackageUpdate(BaseModel):
    category_id: int
    name: str
    package_type: str | None = None
    default_price: float
    is_active: bool = True


class PackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    package_code: str
    category_id: int
    category_name: str
    name: str
    package_type: str | None
    default_price: float
    is_active: bool
    created_at: datetime


class PackagePriceHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    package_id: int
    effective_from: date
    effective_to: date | None
    price: float
