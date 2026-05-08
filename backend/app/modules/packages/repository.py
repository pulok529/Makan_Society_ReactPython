from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.packages.models import Package, PackagePriceHistory


class PackageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_packages(self) -> list[Package]:
        statement = select(Package).order_by(Package.name.asc())
        return list(self.db.scalars(statement))

    def get_by_name(self, name: str) -> Package | None:
        statement = select(Package).where(Package.name == name)
        return self.db.scalar(statement)

    def get_by_id(self, package_id: int) -> Package | None:
        return self.db.get(Package, package_id)

    def add(self, package: Package) -> Package:
        self.db.add(package)
        self.db.flush()
        self.db.refresh(package)
        return package

    def add_price_history(self, history: PackagePriceHistory) -> PackagePriceHistory:
        self.db.add(history)
        self.db.flush()
        self.db.refresh(history)
        return history
