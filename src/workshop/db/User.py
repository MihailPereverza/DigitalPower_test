from ormar import Model
from ormar import Integer, String

from src.workshop.db.connection import metadata
from src.workshop.db.connection import database


class User(Model):
    class Meta:
        metadata = metadata
        database = database
        tablename = 'users'

    id: int = Integer(primary_key=True, autoincrement=True, nullable=False)
    username: str = String(max_length=20, unique=True, nullable=False)
    password_hash: str = String(max_length=200, nullable=False)
