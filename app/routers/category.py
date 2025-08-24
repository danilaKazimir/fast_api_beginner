from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert
from slugify import slugify

from app.backend.db_depends import get_db
from app.schemas import CreateCategory
from app.models.category import Category
from app.routers.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["category"])


@router.get("/")
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await db.scalars(select(Category).where(Category.is_active == True))
    return categories.all()


@router.post("/")
async def create_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: CreateCategory,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin"):
        await db.execute(
            insert(Category).values(
                name=body.name,
                parent_id=body.parent_id,
                slug=slugify(body.name),
            )
        )
        await db.commit()
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission",
        )


@router.put("/")
async def update_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: int,
    body: CreateCategory,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin"):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no category found",
            )

        category.name = body.name
        category.slug = slugify(body.name)
        category.parent_id = body.parent_id
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Category update is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission",
        )


@router.delete("/")
async def delete_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin"):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no category found",
            )
        category.is_active = False
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Category delete is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission",
        )
