from app.db.database import Base
from sqlalchemy import Column, Integer, String , DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name  = Column(String,nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    hashed_password  = Column(String,nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    plan = Column(String,default="free")
    is_active = Column(Boolean,default=True)
    plan_expires_at = Column(DateTime, default=None)
    api_key  = Column(String, nullable=True,default=None, unique=True)
    is_verified = Column(Boolean,default=False)
    verification_token = Column(String, default=None)

    databases = relationship("Database", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email}, plan={self.plan})>"