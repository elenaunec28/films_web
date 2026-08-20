import pymysql
from local_settings import dbconfig


def get_sql_connection():
    """Создаёт подключение к MySQL с курсором, возвращающим словари."""
    connection = pymysql.connect(
        **dbconfig,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def execute_query(connection, query, params=None, fetch_one=False):
    """
    fetch_one=True — вернуть одну строку (словарь или None),
    иначе — список строк.
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()


def search_by_keyword(connection, keyword, limit=10, offset=0):
    """Возвращает фильмы, у которых ключевое слово встречается в названии."""
    query = """
        SELECT
            film.film_id,
            film.title,
            film.release_year,
            category.name AS genre
        FROM film
        JOIN film_category
            ON film.film_id = film_category.film_id
        JOIN category
            ON film_category.category_id = category.category_id
        WHERE film.title LIKE %s
        ORDER BY film.title
        LIMIT %s OFFSET %s
    """
    search_pattern = f"%{keyword}%"

    return execute_query(connection, query, (search_pattern, limit, offset))


def get_all_genres(connection):
    """Возвращает список названий всех жанров."""
    query = """
        SELECT name 
        FROM category
    """

    rows = execute_query(connection, query)

    return [row['name'] for row in rows]


def get_year_range(connection):
    """Возвращает минимальный и максимальный год выпуска в базе."""
    query = """
        SELECT MIN(release_year) AS min_year, MAX(release_year) AS max_year
        FROM film
    """

    return execute_query(connection, query, fetch_one=True)


def search_by_genre_and_year(connection, genre, start_year, end_year,
                                                limit=10, offset=0):
    """Возвращает фильмы указанного жанра за диапазон годов."""
    query = """
        SELECT 
            film.film_id,
            film.title,
            film.release_year,
            category.name AS genre
        FROM film
        JOIN film_category
            ON film.film_id = film_category.film_id
        JOIN category
            ON film_category.category_id = category.category_id
        WHERE category.name = %s
        AND film.release_year BETWEEN %s AND %s
        ORDER BY film.title
        LIMIT %s OFFSET %s
    """

    params = (genre, start_year, end_year, limit, offset)

    return execute_query(connection, query, params)


def count_by_keyword(connection, keyword):
    """Возвращает количество фильмов, по ключевому слову."""
    query = """
        SELECT COUNT(*) AS total
        FROM film
        WHERE title LIKE %s
    """
    search_pattern = f"%{keyword}%"
    result = execute_query(connection, query, (search_pattern,), fetch_one=True)

    return result['total']


def count_by_genre_and_year(connection, genre, start_year, end_year):
    """Возвращает количество фильмов по жанру и диапазону годов."""
    query = """
        SELECT COUNT(*) AS total
        FROM film
        JOIN film_category
            ON film.film_id = film_category.film_id
        JOIN category
            ON film_category.category_id = category.category_id
        WHERE category.name = %s
        AND film.release_year BETWEEN %s AND %s
    """
    params = (genre, start_year, end_year)
    result = execute_query(connection, query, params, fetch_one=True)

    return result['total']


if __name__ == "__main__":
    with get_sql_connection() as connection:
        print("--- Диапазон годов ---")
        print(get_year_range(connection))

        print("--- Жанры ---")
        print(get_all_genres(connection))

        print("--- Поиск по слову ---")
        print(search_by_keyword(connection, "love", limit=3))

        print("--- Всего по слову ---")
        print(count_by_keyword(connection, "love"))

        print("--- Поиск по жанру ---")
        print(search_by_genre_and_year(connection, "Action", 2005, 2010,
                                       limit=3))