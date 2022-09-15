import sqlite3
from datetime import datetime
from loader import bot
from loguru import logger


def db_write(user_id: int, search_results: list) -> None:
    """
    Функция записывает историю результатов поиска в базу данных SQL
    :param user_id: (int) user-ID пользователя телеграм, сделавшего запрос
    :param search_results: (list) список результатов поиска
    :return: None
    """
    with sqlite3.connect('history.db') as con:
        cur = con.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS '{user_id}' (
                    info TEXT,
                    pics TEXT
                    )""")
        search_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
        with bot.retrieve_data(user_id) as data:
            cur.execute(f"INSERT INTO '{user_id}' VALUES ('{data['command']} {search_time}', NULL)")
        for hotel in search_results:
            pics = ' '.join(hotel.pics_list)
            cur.execute(f'INSERT INTO "{user_id}" VALUES ("{hotel.info}", "{pics}")')
        logger.debug("Search results added to history database")


def db_read(user_id: int) -> tuple:
    """
    Функция возвращает очередные результаты поиска из истории для данного пользователя телеграм
    :param user_id: (int) user-ID пользователя телеграм, сделавшего запрос
    :return: (tuple) очередной результат поиска из истории запросов для заданного пользователя
    """
    with sqlite3.connect('history.db') as con:
        cur = con.cursor()
        with bot.retrieve_data(user_id) as data:
            if data['history'][0] == 0:
                cur.execute(f"SELECT max(rowid) FROM '{user_id}'")
                end_search = cur.fetchone()[0]
                cur.execute(f"SELECT min(rowid) FROM '{user_id}'")
                data['history'][0] = cur.fetchone()[0]
            else:
                end_search = data['history'][1]

        cur.execute(f"SELECT max(rowid), info FROM '{user_id}' WHERE info LIKE '/%' AND rowid < {end_search}")
        start_search = cur.fetchone()
        cur.execute(f"SELECT * FROM '{user_id}' WHERE rowid > {start_search[0]} AND rowid <= {end_search}")
        result = cur.fetchall()
        with bot.retrieve_data(user_id) as data:
            data['history'][1] = start_search[0] - 1

        return start_search[1], result


