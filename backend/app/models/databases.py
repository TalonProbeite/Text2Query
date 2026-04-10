from app.db.database import Base
from sqlalchemy import Column, Integer, String , Boolean , ForeignKey
from sqlalchemy.orm import relationship




class Database(Base):

    __tablename__ = "databases"

    id = Column(Integer, primary_key=True, index=True)
    dialect = Column(String, nullable=False)
    database_alias  = Column(String,nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer , nullable=False)
    database_name = Column(String, nullable=False)
    db_username = Column(String, nullable=False)
    ssl = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="databases")