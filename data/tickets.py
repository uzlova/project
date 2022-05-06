import sqlalchemy
from .db_session import SqlAlchemyBase


class Tickets(SqlAlchemyBase):
    __tablename__ = 'tickets'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True, unique=True)
    title_of_film = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("films.id"))
    date = sqlalchemy.Column(sqlalchemy.Date)
    time = sqlalchemy.Column(sqlalchemy.Time)

    def __repr__(self):
        return f"{self.id}, {self.date}, {self.time}"

    def get_time(self):
        return [self.time]