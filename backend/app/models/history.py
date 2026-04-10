from app.db.database import Base
from sqlalchemy import Column, BigInteger, String , Boolean , ForeignKey , DateTime , Integer  , Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


class QueryHistory(Base):
    __tablename__ = "history"

    id = Column(BigInteger, primary_key=True, index=True)
    prompt = Column(Text , nullable=False)
    query = Column(Text , nullable=False)
    is_danger = Column(Boolean, nullable=False)
    dialect = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="history")

    __table_args__ = (
        Index("idx_history_user_created", "user_id", "created_at"),
    )