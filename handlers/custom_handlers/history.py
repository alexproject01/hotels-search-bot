from time import sleep
from sqlite3 import OperationalError

from loguru import logger
from telebot.types import Message, InputMediaPhoto

from loader import bot
from states.search_params import UserParamState
from keyboards.reply.history_next_result import history_next
from database.data_base import db_read


@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    # Обработчик команды /history
    logger.debug("User {} started /history command", message.from_user.id)
    bot.set_state(message.from_user.id, UserParamState.history)
    with bot.retrieve_data(message.from_user.id) as data:
        data['history'] = [0, 0]
    next_search(message)


@bot.message_handler(state=UserParamState.history)
def next_search(message: Message) -> None:
    # Обработчик следующего шага поиска результатов истории
    if message.text in ('Да', '/history'):
        try:
            result = db_read(message.from_user.id)
            logger.debug("Next results from history displayed for User {}", message.from_user.id)
            bot.send_message(message.from_user.id, result[0])
            for entry in result[1]:
                sleep(0.5)
                bot.send_message(message.from_user.id, f'{entry[0]}', disable_web_page_preview=True)
                if entry[1] != '':
                    pics = entry[1].split()
                    image_lst = [InputMediaPhoto(image) for image in pics]
                    bot.send_media_group(message.from_user.id, image_lst)
            with bot.retrieve_data(message.from_user.id) as data:
                if data['history'][0] < data['history'][1]:
                    bot.send_message(message.from_user.id,
                                     'Показать следующие результаты?', reply_markup=history_next())
                    sleep(1)
                else:
                    logger.debug("User {} reached the end of history", message.from_user.id)
                    bot.send_message(message.from_user.id, 'Вы просмотрели всю сохраненную историю поиска \U00002705')
                    bot.delete_state(message.from_user.id)
        except OperationalError as ex:
            bot.send_message(message.from_user.id, 'Отсутствует информация об истории запросов \U0000274C')
            bot.delete_state(message.from_user.id)
            logger.warning("SQL database error: {}", ex)
    elif message.text == 'Нет':
        logger.debug("User {} stopped browsing history results", message.from_user.id)
        bot.send_message(message.from_user.id, 'Вы остановили просмотр истории запросов')
        bot.delete_state(message.from_user.id)
    else:
        bot.send_message(message.from_user.id, 'Показать следующие результаты из истории? '
                                               '\nСделайте выбор, нажав на кнопку', reply_markup=history_next())
