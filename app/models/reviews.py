from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, CheckConstraint

from app.backend.db import Base


class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    comment = Column(String, nullable=True)
    comment_date = Column(DateTime, default=datetime.now)
    grade = Column(Integer)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("grade BETWEEN 1 AND 5", name="ck_reviews_grade_1_5"),
    )
