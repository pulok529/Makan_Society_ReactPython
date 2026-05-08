from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.categories.repository import CategoryRepository
from app.modules.packages.models import Package, PackagePriceHistory
from app.modules.packages.repository import PackageRepository
from app.modules.packages.schemas import PackageCreate, PackageUpdate


class PackageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PackageRepository(db)
        self.category_repository = CategoryRepository(db)

    def list_packages(self) -> list[Package]:
        return self.repository.list_packages()

    def create_package(self, payload: PackageCreate) -> Package:
        category = self.category_repository.get_by_id(payload.category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        if self.repository.get_by_name(payload.name.strip()) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Package name already exists",
            )

        package = Package(
            category_id=payload.category_id,
            name=payload.name.strip(),
            package_type=payload.package_type.strip() if payload.package_type else None,
            default_price=payload.default_price,
            is_active=payload.is_active,
        )
        self.repository.add(package)
        self.repository.add_price_history(
            PackagePriceHistory(
                package_id=package.id,
                effective_from=date.today(),
                effective_to=None,
                price=payload.default_price,
            )
        )
        self.db.commit()
        return package

    def update_package(self, package_id: int, payload: PackageUpdate) -> Package:
        package = self.repository.get_by_id(package_id)
        if package is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

        category = self.category_repository.get_by_id(payload.category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        existing = self.repository.get_by_name(payload.name.strip())
        if existing is not None and existing.id != package_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Package name already exists")

        package.category_id = payload.category_id
        package.name = payload.name.strip()
        package.package_type = payload.package_type.strip() if payload.package_type else None
        package.default_price = payload.default_price
        package.is_active = payload.is_active
        self.repository.add_price_history(
            PackagePriceHistory(
                package_id=package.id,
                effective_from=date.today(),
                effective_to=None,
                price=payload.default_price,
            )
        )
        self.db.commit()
        return package
