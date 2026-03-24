from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from datetime import datetime

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(BigInteger, unique=True)

    name = Column(String)
    birthdate = Column(String)
    zodiac = Column(String)

    balance = Column(Integer, default=30)

    last_daily_bonus = Column(DateTime, nullable=True)
    last_card_of_day = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)