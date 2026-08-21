import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Клиент для запросов к приложению."""
    return TestClient(app)


def test_app_starts(client):
    """Приложение отвечает на запрос главной страницы."""
    response = client.get("/")

    assert response.status_code == 200


def test_search_keyword_responds(client):
    """Поиск по слову отвечает без ошибки сервера."""
    response = client.post("/search/keyword", data={"keyword": "a"})

    assert response.status_code == 200


def test_search_genre_responds(client):
    """Поиск по жанру отвечает без ошибки сервера."""
    response = client.post("/search/genre-only", data={"genre": "Comedy"})

    assert response.status_code == 200


def test_search_genre_year_responds(client):
    """Поиск по жанру и годам отвечает без ошибки сервера."""
    response = client.post("/search/genre", data={
        "genre": "Action", "year_from": 2000, "year_to": 2010,
    })

    assert response.status_code == 200


def test_stats_responds(client):
    """Страница статистики отвечает без ошибки сервера."""
    response = client.get("/stats")

    assert response.status_code == 200


def test_mysql_available():
    """Подключение к MySQL работает."""
    from mysql_connector import get_sql_connection, get_all_genres

    with get_sql_connection() as connection:
        genres = get_all_genres(connection)

    assert len(genres) > 0


def test_mongo_available():
    """Подключение к MongoDB работает."""
    from log_stats import get_popular_searches

    result = get_popular_searches()

    assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])