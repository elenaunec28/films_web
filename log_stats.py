from pymongo.errors import PyMongoError

from log_writer import get_mongo_connection


def get_recent_searches(limit=5):
    """Возвращает последние уникальные поисковые запросы."""
    pipeline = [
        {"$group": {
            "_id": {
                "search_type": "$search_type",
                "params": "$params"
            },
            "last_time": {"$max": "$timestamp"},
            "results_count": {"$max": "$results_count"}
        }},
        {"$sort": {"last_time": -1}},
        {"$limit": limit}
    ]

    collection = get_mongo_connection()
    return list(collection.aggregate(pipeline))



def get_popular_searches(limit=5):
    """Возвращает самые частые поисковые запросы.
    Группирует одинаковые запросы (тип + параметры) и считает,
    сколько раз каждый из них выполнялся."""
    pipeline = [
        {"$group": {
            "_id": {
                "search_type": "$search_type",
                "params": "$params"
            },
            "count": {"$sum": 1},
            "results_count": {"$max": "$results_count"},
            "last_time": {"$max": "$timestamp"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    collection = get_mongo_connection()
    return list(collection.aggregate(pipeline))



if __name__ == "__main__":
    print("--- Последние запросы ---")
    for item in get_recent_searches():
        print(item)

    print("--- Популярные запросы ---")
    for item in get_popular_searches():
        print(item)
