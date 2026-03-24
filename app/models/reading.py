from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime

from app.db.base import Base


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    question = Column(String, nullable=True)
    cards = Column(String)  # JSON строка
    answer = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)