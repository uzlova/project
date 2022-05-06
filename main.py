import datetime
import os

import bs4
import requests
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
DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


def get_new_tickets():
    session = db_session.create_session()
    films_titles = []
    date = datetime.date.today()
    films = session.query(Films).all()
    for i in films:
        films_titles.append(i.title)
    s = requests.get(f'https://www.kinopoisk.ru/afisha/city/7117/day_view/{date}/')
    b = bs4.BeautifulSoup(s.text, "html.parser")
    a = b.getText()
    a = a[a.find('список фильмов') + len('список фильмов'):a.find('фильм:')]

    with open('input.txt', 'w') as f:
        f.write(a)
    with open('input.txt') as f:
        lines = [i.strip() for i in f.readlines() if len(i.strip())]

    films = {}
    name = ''
    index = 1
    flag = False
    flag2 = False
    while index < len(lines):
        if flag:
            if 'мин' in lines[index] and lines[index][:lines[index].find('мин') - 1].isdigit():
                flag = False
            index += 1
            continue
        else:
            for i in ['Дом Кино']:
                if i == lines[index]:
                    films[name].append([])
                    index += 1
                    flag2 = True
                    break
            if flag2:
                flag2 = False
                continue
            if '3D' in lines[index]:
                for i in range(0, len(lines[index]) - 2, 5):
                    time = lines[index][i:i + 5]
                    time = time.split(':')
                    time = datetime.time(hour=int(time[0]), minute=int(time[1]), second=0)
                    films[name][-1].append(time)
            else:
                for day in DAYS:
                    if lines[index][:len(day)] == day:
                        flag2 = True
                        break
                if flag2:
                    break
                for i in range(len(lines[index])):
                    if lines[index][i].isalpha():
                        flag2 = True
                        break
                if flag2:
                    films[lines[index]] = []
                    name = lines[index]
                    flag = True
                    index += 1
                    flag2 = False
                    continue
                for i in range(0, len(lines[index]) - 2, 5):
                    time = lines[index][i:i + 5]
                    time = time.split(':')
                    time = datetime.time(hour=int(time[0]), minute=int(time[1]), second=0)
                    films[name][-1].append(time)
        index += 1
    for key, value in films.items():
        if key in films_titles:
            film = session.query(Films).filter(Films.title == key).first()
            for list_time in value:
                for item in list_time:
                    ticket = Tickets(title_of_film=film.id, date=date, time=item.replace(microsecond=0))
                    session.add(ticket)
                    session.commit()


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
    if old_tickets:
        for item in old_tickets:
            session.delete(item)
        session.commit()
        return True
    else:
        return False


@app.route('/')
def index():
    if delete_old_tickets():
        get_new_tickets()
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


if __name__ == '__main__':
    db_session.global_init("db/cinema.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
