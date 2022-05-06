import sqlalchemy
from .db_session import SqlAlchemyBase


class Genres(SqlAlchemyBase):
    __tablename__ = 'genres'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True, unique=True)
    genre = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return self.genre