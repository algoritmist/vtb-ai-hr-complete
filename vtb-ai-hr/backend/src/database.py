from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

import recruiter.models
import common.models
import candidate.models

engine = create_engine(
    "postgresql+psycopg2://postgres:postgres@localhost:5432/default", echo=True)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)
print("Tables: ", Base.metadata.tables.keys())
