from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    phone = Column(String)
    position = Column(String)
    is_admin = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

    def __repr__(self):
        return f"<User(full_name='{self.full_name}', position='{self.position}')>"