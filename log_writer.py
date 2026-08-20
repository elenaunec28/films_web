from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from local_settings import MONGODB_URL_WRITE

def get_mongo_connection():
    """Подключается к MongoDB и возвращает коллекцию для логов."""
    client = MongoClient(MONGODB_URL_WRITE)

    db = client["ich_edit"]

    collection = db["final_project_030626ptm_elena_ukrainets"]

    return collection


def save_search_log(search_type, params, results_count):
    """Записывает информацию о поисковом запросе в MongoDB."""
    log = {
        "timestamp": datetime.now(),
        "search_type": search_type,
        "params": params,
        "results_count": results_count
    }

    try:
        collection = get_mongo_connection()
        collection.insert_one(log)
    except PyMongoError as error:
        print(f"Не удалось записать лог: {error}")

if __name__ == "__main__":
    save_search_log("keyword", {"keyword": "dog"}, 2)
    print("Лог записан")