from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

from pymongo.errors import PyMongoError

import pymysql

from mysql_connector import (
    get_sql_connection,
    get_all_genres,
    get_year_range,
    search_by_keyword,
    count_by_keyword,
    search_by_genre_and_year,
    count_by_genre_and_year,
)
from log_writer import save_search_log
from log_stats import get_popular_searches, get_recent_searches

app = FastAPI()
templates = Jinja2Templates(directory="templates")

PER_PAGE = 10


def error_page(request, message, status_code=503):
    """Возвращает страницу с сообщением об ошибке."""
    return templates.TemplateResponse(request, "error.html", {
        "message": message,
    }, status_code=status_code)


@app.get("/")
def home(request: Request):
    """Главная страница со списком жанров."""
    try:
        with get_sql_connection() as connection:
            genres = get_all_genres(connection)
            years = get_year_range(connection)
    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    return templates.TemplateResponse(request, "home.html", {
        "genres": genres,
        "years": years,
    })


@app.post("/search/keyword")
def search_keyword(request: Request, keyword: str = Form(...)):
    """Поиск по ключевому слову, первая страница результатов."""
    keyword = keyword.strip().lower()
    if not keyword:
        return error_page(request, "Введите ключевое слово для поиска.", 400)

    try:
        with get_sql_connection() as connection:
            total = count_by_keyword(connection, keyword) # COUNT(*), без LIMIT
            films = search_by_keyword(connection, keyword, limit=PER_PAGE, offset=0) # с LIMIT

    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    save_search_log("keyword", {"keyword": keyword}, total)

    return templates.TemplateResponse(request, "films_table.html", {
        "films": films,
        "total": total,
        "page": 1,
        "pages": (total + PER_PAGE - 1) // PER_PAGE,
        "keyword": keyword,
    })


@app.get("/search/keyword")
def search_keyword_page(request: Request, keyword: str, page: int = 1):
    """Страница результатов поиска по ключевому слову."""
    if page < 1:
        page = 1

    offset = (page - 1) * PER_PAGE

    try:
        with get_sql_connection() as connection:
            total = count_by_keyword(connection, keyword)
            films = search_by_keyword(connection, keyword, limit=PER_PAGE, offset=offset)

    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    return templates.TemplateResponse(request, "films_table.html", {
        "films": films,
        "total": total,
        "page": page,
        "pages": (total + PER_PAGE - 1) // PER_PAGE,
        "keyword": keyword,
    })


@app.post("/search/genre")
def search_genre(request: Request,
                 genre: str = Form(...),
                 year_from: int = Form(...),
                 year_to: int = Form(...)):
    """Поиск по жанру и диапазону годов, первая страница."""
    if year_from > year_to:
        year_from, year_to = year_to, year_from

    params = {"genre": genre, "year_from": year_from, "year_to": year_to}

    try:
        with get_sql_connection() as connection:
            total = count_by_genre_and_year(connection, genre, year_from, year_to)
            films = search_by_genre_and_year(connection, genre, year_from, year_to,
                                            limit=PER_PAGE, offset=0)
    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    save_search_log("genre_and_year", params, total)

    return templates.TemplateResponse(request, "films_table.html", {
        "films": films,
        "total": total,
        "page": 1,
        "pages": (total + PER_PAGE - 1) // PER_PAGE,
        "genre": genre,
        "year_from": year_from,
        "year_to": year_to,
    })


@app.get("/search/genre")
def search_genre_page(request: Request, genre: str,
                      year_from: int, year_to: int, page: int = 1):
    """Страница результатов поиска по жанру и годам."""
    if page < 1:
        page = 1

    offset = (page - 1) * PER_PAGE

    try:
        with get_sql_connection() as connection:
            total = count_by_genre_and_year(connection, genre, year_from, year_to)
            films = search_by_genre_and_year(connection, genre, year_from, year_to,
                                            limit=PER_PAGE, offset=offset)
    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    return templates.TemplateResponse(request, "films_table.html", {
        "films": films,
        "total": total,
        "page": page,
        "pages": (total + PER_PAGE - 1) // PER_PAGE,
        "genre": genre,
        "year_from": year_from,
        "year_to": year_to,
    })


@app.post("/search/genre-only")
def search_genre_only(request: Request, genre: str = Form(...)):
    """Поиск только по жанру, без ограничения по годам."""
    try:
        with get_sql_connection() as connection:
            years = get_year_range(connection)
            year_from = years["min_year"]
            year_to = years["max_year"]

            total = count_by_genre_and_year(connection, genre, year_from, year_to)
            films = search_by_genre_and_year(connection, genre, year_from, year_to,
                                        limit=PER_PAGE, offset=0)
    except pymysql.MySQLError as e:
        return error_page(request, f"База данных недоступна: {e}")

    save_search_log("genre", {"genre": genre}, total)

    return templates.TemplateResponse(request, "films_table.html", {
        "films": films,
        "total": total,
        "page": 1,
        "pages": (total + PER_PAGE - 1) // PER_PAGE,
        "genre": genre,
        "year_from": year_from,
        "year_to": year_to,
    })


@app.get("/stats")
def stats(request: Request, kind: str = "popular"):
    """Статистика запросов: популярные или последние."""
    try:
        if kind == "recent":
            items = get_recent_searches()
            title = "Последние 5 уникальных запросов"
        else:
            items = get_popular_searches()
            title = "Топ-5 популярных запросов"
    except PyMongoError as e:
        print(f"Ошибка MongoDB: {e}")
        return error_page(request, "Не удалось получить статистику: "
                                   "база логов недоступна.")

    return templates.TemplateResponse(request, "statistics.html", {
        "items": items,
        "title": title,
        "kind": kind,
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)