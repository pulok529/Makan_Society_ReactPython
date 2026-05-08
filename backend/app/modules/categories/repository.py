from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.categories.models import MemberCategory


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> list[MemberCategory]:
        statement = select(MemberCategory).order_by(MemberCategory.code.asc(), MemberCategory.name.asc())
        return list(self.db.scalars(statement))

    def get_by_name(self, name: str) -> MemberCategory | None:
        statement = select(MemberCategory).where(MemberCategory.name == name)
        return self.db.scalar(statement)

    def get_by_id(self, category_id: int) -> MemberCategory | None:
        return self.db.get(MemberCategory, category_id)

    def add(self, category: MemberCategory) -> MemberCategory:
        self.db.add(category)
        self.db.flush()
        self.db.refresh(category)
        return category
