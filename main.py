import datetime

from flask import Flask, render_template, request
from werkzeug.utils import redirect
from data.films import Films
from data import db_session
from data.tickets import Tickets
from data.register import RegisterForm
from data.users import User
import locale

locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def get_date(date):
    date = str(date)
    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    date_list = date.split('-')
    return f"{date_list[2]} {month_list[int(date_list[1]) - 1]}"


def delete_old_tickets():
    date = datetime.date.today()
    time = datetime.datetime.now().time()
    session = db_session.create_session()
    old_tickets = session.query(Tickets).filter(Tickets.date < date).all()
    old_times = session.query(Tickets).filter(Tickets.date == date, Tickets.time < time).all()
    for item in old_tickets:
        session.delete(item)
    for item in old_times:
        session.delete(item)
    session.commit()


@app.route('/')
def index():
    delete_old_tickets()
    movies_today = []
    session = db_session.create_session()
    date = datetime.date.today()
    films_today = session.query(Tickets, Films).filter(Tickets.date == date, Films.id == Tickets.title_of_film).all()
    for i in films_today:
        if i[1] not in movies_today:
            movies_today.append(i[1])
    today = get_date(str(date))
    return render_template("index.html", today=today, movies_today=movies_today)


@app.route('/schedule/<date>')
@app.route('/schedule')
def schedule(date=datetime.date.today()):
    if date.__class__ == datetime.datetime:
        date = date.date()  # если date это объект класса datetime.datetime, то необходимо его преобразовать,
        # чтобы date была формата y-m-d, а не y-m-d H:M:S
    films = {}  # в словаре: ключ - название фильма, значения [img, title, genre, {id билета: time}]
    session = db_session.create_session()
    films_today = session.query(Tickets, Films).filter(Tickets.date == date, Films.id == Tickets.title_of_film).all()
    for i in films_today:
        if i[1] not in films.keys():
            films[i[1]] = [i[1].img, i[1].title, i[1].genre, {}]
            time = ':'.join(str(i[0].time).split(':')[:2])
            films[i[1]][-1][i[0].id] = time
        else:
            time = ':'.join(str(i[0].time).split(':')[:2])
            films[i[1]][-1][i[0].id] = time

    date = datetime.date.today()
    _tomorrow = (date + datetime.timedelta(days=1))
    _after_tomorrow = (date + datetime.timedelta(days=2))
    tomorrow = get_date(_tomorrow)
    after_tomorrow = get_date(_after_tomorrow)

    today = get_date(date)
    return render_template("schedule.html", today=today, tomorrow=tomorrow, _tomorrow=_tomorrow,
                           after_tomorrow=after_tomorrow, _after_tomorrow=_after_tomorrow,
                           films=films)


@app.route('/movie/<name>')
def movie(name):
    date_list = []
    session = db_session.create_session()
    film = session.query(Films).filter(Films.title == name).first()
    tickets = session.query(Tickets).filter(Tickets.title_of_film == int(film.list()[0])).all()
    for i in tickets:
        print(i.__class__)
    for i in tickets:
        i_id = i.id
        t = f"{i.time.hour}:{i.time.minute}"
        dt = get_date(i.date)
        date_list.append([dt, t, i_id])
    return render_template("movie.html", imgs=film.img, title=film.title, genre=film.genre, director=film.director,
                           time=film.time, rating=film.rating, description=film.description, date_list=date_list)


@app.route("/buy_ticket/<int:id>", methods=["POST", "GET"])
def buy_ticket(id):
    session = db_session.create_session()
    ticket = session.query(Tickets).filter(Tickets.id == id).first()
    film = session.query(Tickets, Films).filter(Tickets.id == id, Tickets.title_of_film == Films.id).first()
    form = RegisterForm()
    if form.validate_on_submit():
        user = User()
        user.phone = form.phone.data
        user.name = form.name.data
        session.add(user)
        session.commit()
        return redirect("/successful_purchase")
    return render_template("buy_ticket.html", _img=film[1].img, date=ticket.date, time=ticket.time,
                           title=film[1].title, form=form)


@app.route("/successful_purchase")
def successful_purchase():
    return render_template("successful_purchase.html")


@app.route('/address')
def address():
    return render_template("adress.html")


@app.route('/movies')
def movies():
    session = db_session.create_session()
    movies = session.query(Films).all()
    return render_template("movies.html", movies=movies)


def main():
    db_session.global_init("db/cinema.db")
    app.run()


if __name__ == '__main__':
    main()
