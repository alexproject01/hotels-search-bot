import os

from dotenv import load_dotenv, find_dotenv
from loguru import logger


logger.add('logs.log', level='DEBUG', mode='w')
if not find_dotenv():
    logger.error("File .env not found")
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found")
    exit("Отсутствует токен бота в файле .env")
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
if not RAPID_API_KEY:
    logger.error("RAPID_API_KEY not found")
    exit("Отсутствует ключ RAPID API в файле .env")
DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("help", "Cправка"),
    ("lowprice", "Найти дешевые отели"),
    ("highprice", "Найти дорогие отели"),
    ("bestdeal", "Наиболее выгодные предложения"),
    ("history", "Вывести историю поиска")
)
