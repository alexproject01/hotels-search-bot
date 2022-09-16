import json
import re

import requests
from loguru import logger

from config_data import config


def api_request(api_url: str, querystring: dict) -> dict:
    """
    Функция делает запрос к API на основании переданных параметров и возвращает ответ сервера
    :param api_url: (str) адрес API
    :param querystring: (dict) словарь с поисковыми параметрами
    :return: (dict) результат ответа API после проверки на наличие ключей и десериализации
    """
    for _ in range(3):
        try:
            response = requests.get(url=api_url,
                                    params=querystring,
                                    headers={'X-RapidAPI-Key': config.RAPID_API_KEY,
                                             'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'
                                             },
                                    timeout=10)
            logger.debug("response status code: {}", response.status_code)
            if response.status_code == requests.codes.ok:
                pattern1 = r'(?<="CITY_GROUP",).+?[\]]'
                pattern2 = r'(?<="searchResults":).+?[\]]'
                pattern3 = r'(?<="hotelImages":).+?[\]]'
                find1 = re.search(pattern1, response.text)
                find2 = re.search(pattern2, response.text)
                find3 = re.search(pattern3, response.text)
                if find1 or find2 or find3:
                    logger.debug("Response from API address {} is valid", api_url)
                    result = json.loads(response.text)
                    return result
                logger.warning("Response from API address {} is invalid", api_url)
        except requests.exceptions.ReadTimeout:
            logger.warning("Request exception: read timed out")
    return None
