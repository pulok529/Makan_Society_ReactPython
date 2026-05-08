from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.categories.service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryRead]:
    service = CategoryService(db)
    return [CategoryRead.model_validate(category) for category in service.list_categories()]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("members:manage"))],
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
) -> CategoryRead:
    service = CategoryService(db)
    category = service.create_category(payload)
    return CategoryRead.model_validate(category)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_permission("members:manage"))],
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryRead:
    service = CategoryService(db)
    category = service.update_category(category_id, payload)
    return CategoryRead.model_validate(category)
