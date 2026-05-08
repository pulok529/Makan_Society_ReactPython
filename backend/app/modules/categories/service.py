from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.categories.models import MemberCategory
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CategoryRepository(db)

    def list_categories(self) -> list[MemberCategory]:
        return self.repository.list_categories()

    def create_category(self, payload: CategoryCreate) -> MemberCategory:
        if self.repository.get_by_name(payload.name.strip()) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category name already exists",
            )

        category = MemberCategory(
            name=payload.name.strip(),
            code=payload.code.strip() if payload.code else None,
            is_active=payload.is_active,
        )
        self.repository.add(category)
        self.db.commit()
        return category

    def update_category(self, category_id: int, payload: CategoryUpdate) -> MemberCategory:
        category = self.repository.get_by_id(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        existing = self.repository.get_by_name(payload.name.strip())
        if existing is not None and existing.id != category_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")

        category.name = payload.name.strip()
        category.code = payload.code.strip() if payload.code else None
        category.is_active = payload.is_active
        self.db.commit()
        return category
