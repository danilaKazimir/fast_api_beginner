from typing import Annotated
from statistics import fmean

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Product
from app.models.reviews import Reviews
from app.routers.auth import get_current_user
from app.schemas import CreateReview

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/")
async def all_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sql = select(Reviews).where(Reviews.is_active.is_(True))
    reviews = (await db.scalars(sql)).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found!")
    return reviews


@router.get("/{product_slug")
async def products_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
):
    sql = (
        select(Reviews)
        .join(Product, Product.id == Reviews.product_id)
        .where(Product.slug == product_slug, Reviews.is_active.is_(True))
    )
    reviews = (await db.scalars(sql)).all()
    if not reviews:
        raise HTTPException(
            status_code=404, detail=f"No reviews found for {product_slug}!"
        )
    return reviews


@router.post("/")
async def add_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    body: CreateReview,
):
    if get_user.get("is_customer"):
        sql = select(Product).where(
            Product.is_active.is_(True), Product.slug == body.product_slug
        )
        product = await db.scalar(sql)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"No product {body.product_slug} found!"
            )
        await db.execute(
            insert(Reviews).values(
                user_id=get_user.get("user_id"),
                product_id=product.id,
                comment=body.comment,
                grade=body.grade,
            )
        )

        reviews = await products_reviews(db, body.product_slug)
        grades = [review.grade for review in reviews]
        product.rating = round(fmean(grades), 1)

        await db.commit()

        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    else:
        raise HTTPException(
            status_code=404, detail="Only customers are able to create reviews!"
        )


@router.delete("/{review_id}")
async def delete_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    review_id: int,
):
    if get_user.get("is_admin"):
        sql = select(Reviews).where(Reviews.id == review_id)
        review = await db.scalar(sql)
        if not review:
            raise HTTPException(
                status_code=404, detail=f"No review with {review_id} id found!"
            )
        review.is_active = False
        await db.commit()

        return {"status_code": status.HTTP_204_NO_CONTENT, "transaction": "Successful"}
    else:
        raise HTTPException(status_code=404, detail=f"Only admins can delete reviews!")
