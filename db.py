# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "sqlite:///./bakersdb.db"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Replace these with your cPanel MySQL credentials
MYSQL_USER = "knocknoc_systaio"
MYSQL_PASSWORD = "vmjk*Ka+h=]aAv(j"
MYSQL_HOST = "server.cloudsensy.in"
MYSQL_DB = "knocknoc_bakerys"

# ✅ MySQL connection string (using mysql-connector)
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

# ✅ SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Avoids broken pipe errors
    pool_recycle=280,         # Recycles idle connections before timeout
    pool_size=10,             # Optional: Number of connections to keep in pool
    max_overflow=20           # Optional: Max overflow if pool_size exceeded
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ Dependency for FastAPI (or your app)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
