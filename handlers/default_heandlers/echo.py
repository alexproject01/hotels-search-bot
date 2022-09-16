from telebot.types import Message
from loguru import logger

from loader import bot


@bot.message_handler(commands=[None], func=lambda message: not bot.get_state(message.from_user.id))
def bot_echo(message: Message):
    # Обработчик сообщений от пользователя без заданного состояния
    logger.debug("User {} in state={} sent message '{}'",
                   message.from_user.id, bot.get_state(message.from_user.id), message.text)
    bot.send_message(message.from_user.id, "Справка по командам бота: /help")
