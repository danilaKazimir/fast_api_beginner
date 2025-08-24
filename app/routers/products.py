from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.models import *
from app.routers.auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def all_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    products = await db.scalars(
        select(Product).where(Product.is_active == True, Product.stock > 0)
    )
    all_products = products.all()
    if not all_products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There are no product"
        )
    return all_products


@router.post("/")
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        category = await db.scalar(select(Category).where(Category.id == body.category))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no category found",
            )
        await db.execute(
            insert(Product).values(
                name=body.name,
                description=body.description,
                price=body.price,
                image_url=body.image_url,
                stock=body.stock,
                supplier_id=get_user.get("user_id"),
                category_id=body.category,
                rating=0.0,
                slug=slugify(body.name),
            )
        )
        await db.commit()
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin or supplier permission",
        )


@router.get("/{category_slug}")
async def product_by_category(
    db: Annotated[AsyncSession, Depends(get_db)], category_slug: str
):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    subcategories = await db.scalars(
        select(Category).where(Category.parent_id == category.id)
    )
    categories_and_subcategories = [category.id] + [i.id for i in subcategories.all()]
    products_category = await db.scalars(
        select(Product).where(
            Product.category_id.in_(categories_and_subcategories),
            Product.is_active == True,
            Product.stock > 0,
        )
    )
    return products_category.all()


@router.get("/detail/{product_slug}")
async def product_detail(
    db: Annotated[AsyncSession, Depends(get_db)], product_slug: str
):
    product = await db.scalar(
        select(Product).where(
            Product.slug == product_slug, Product.is_active == True, Product.stock > 0
        )
    )
    if product is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There are no product"
        )
    return product


@router.put("/{product_slug}")
async def update_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    update_product_model: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        product_update = await db.scalar(
            select(Product).where(Product.slug == product_slug)
        )
        if product_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found",
            )
        category = await db.scalar(
            select(Category).where(Category.id == update_product_model.category)
        )
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no category found",
            )

        product_update.name = update_product_model.name
        product_update.description = update_product_model.description
        product_update.price = update_product_model.price
        product_update.image_url = update_product_model.image_url
        product_update.stock = update_product_model.stock
        product_update.category_id = update_product_model.category
        product_update.slug = slugify(update_product_model.name)

        await db.commit()

        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Product update is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin or supplier permission",
        )


@router.delete("/{product_slug}")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        product_delete = await db.scalar(
            select(Product).where(Product.slug == product_slug)
        )
        if product_delete is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found",
            )

        product_delete.is_active = False
        await db.commit()

        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Product delete is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin or supplier permission",
        )
