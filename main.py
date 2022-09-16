from telebot.custom_filters import StateFilter
from telebot.apihelper import ApiTelegramException
from loguru import logger

from loader import bot
import handlers
from utils.set_bot_commands import set_default_commands


if __name__ == '__main__':
    logger.info("Starting bot")
    try:
        bot.add_custom_filter(StateFilter(bot))
        set_default_commands(bot)
        bot.infinity_polling()
    except ApiTelegramException as ex:
        logger.error("{}", ex)
        print("Возникла ошибка при инициализации бота, проверьте корректность токена")
