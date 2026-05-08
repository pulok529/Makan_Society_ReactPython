from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Package(Base):
    __tablename__ = "packages"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("society.member_categories.id"))
    name: Mapped[str] = mapped_column(String(120))
    package_type: Mapped[str | None] = mapped_column(String(100))
    default_price: Mapped[float] = mapped_column(Numeric(18, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PackagePriceHistory(Base):
    __tablename__ = "package_price_history"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("society.packages.id", ondelete="CASCADE"))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    price: Mapped[float] = mapped_column(Numeric(18, 2))
