from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Создаем подключение к базе данных
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL)

# Создаем таблицы
Base.metadata.create_all(engine)

# Создаем сессию
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_admin():
    """Инициализация админского аккаунта при первом запуске"""
    db = SessionLocal()
    from .models import User
    admin = db.query(User).filter(User.is_admin == True).first()
    if not admin:
        admin = User(
            full_name="Administrator",
            password="admin123",  # В реальном приложении нужно хешировать
            is_admin=True
        )
        db.add(admin)
        db.commit()
    db.close()