from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.categories.repository import CategoryRepository
from app.modules.packages.schemas import PackageCreate, PackageRead, PackageUpdate
from app.modules.packages.service import PackageService

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("", response_model=list[PackageRead])
def list_packages(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PackageRead]:
    service = PackageService(db)
    categories = {category.id: category for category in CategoryRepository(db).list_categories()}
    return [
        PackageRead(
            id=package.id,
            package_code=str(package.id),
            category_id=package.category_id,
            category_name=categories[package.category_id].name if package.category_id in categories else "Unknown",
            name=package.name,
            package_type=package.package_type,
            default_price=float(package.default_price),
            is_active=package.is_active,
            created_at=package.created_at,
        )
        for package in service.list_packages()
    ]


@router.post(
    "",
    response_model=PackageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("members:manage"))],
)
def create_package(
    payload: PackageCreate,
    db: Session = Depends(get_db),
) -> PackageRead:
    service = PackageService(db)
    category_repository = CategoryRepository(db)
    package = service.create_package(payload)
    category = category_repository.get_by_id(package.category_id)
    return PackageRead(
        id=package.id,
        package_code=str(package.id),
        category_id=package.category_id,
        category_name=category.name if category is not None else "Unknown",
        name=package.name,
        package_type=package.package_type,
        default_price=float(package.default_price),
        is_active=package.is_active,
        created_at=package.created_at,
    )


@router.put(
    "/{package_id}",
    response_model=PackageRead,
    dependencies=[Depends(require_permission("members:manage"))],
)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    db: Session = Depends(get_db),
) -> PackageRead:
    service = PackageService(db)
    category_repository = CategoryRepository(db)
    package = service.update_package(package_id, payload)
    category = category_repository.get_by_id(package.category_id)
    return PackageRead(
        id=package.id,
        package_code=str(package.id),
        category_id=package.category_id,
        category_name=category.name if category is not None else "Unknown",
        name=package.name,
        package_type=package.package_type,
        default_price=float(package.default_price),
        is_active=package.is_active,
        created_at=package.created_at,
    )
