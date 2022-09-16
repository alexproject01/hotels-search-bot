from loader import bot
from states.search_params import UserParamState
from telebot.types import Message, InputMediaPhoto, CallbackQuery
from keyboards.inline.locations_list import location_choice
from keyboards.reply.guests import guests_amt_choice
from keyboards.reply.results import results_amt_choice
from keyboards.reply.photos import show_pics, pics_amt_choice
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from hotels_api.search import city_id, find_hotels, ApiBadResponse
from database.data_base import db_write
from loguru import logger

LSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def lowprice(message: Message) -> None:
    # Обработчик ввода пользователем одной из поисковых команд
    logger.debug("User {} started {} command", message.from_user.id, message.text)
    bot.set_state(message.from_user.id, UserParamState.location, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text
    bot.send_message(message.from_user.id, f'Введите название локации (язык: русский, английский)')


@bot.message_handler(state=UserParamState.location)
def get_location(message: Message) -> None:
    # Обработчик ввода пользователем названия искомой локации
    logger.debug("User {} location input: {}", message.from_user.id, message.text)
    result_city_id = city_id(message.text)
    if not result_city_id:
        bot.send_message(message.chat.id, 'Город с таким названием не найден в базе.')
        bot.send_message(message.from_user.id, 'Введите название локации (язык: русский, английский):')
        logger.debug("Hotels API respond: locations not found")
    else:
        logger.debug("Hotel API respond: locations found")
        bot.send_message(message.chat.id, text=f'Найдены следующие локации, сделайте выбор:',
                         reply_markup=location_choice(result_city_id))


@bot.callback_query_handler(func=lambda call: bot.get_state(call.from_user.id) == UserParamState.location)
def location_select(call: CallbackQuery):
    # Обработчик выбора пользователем локации из найденных на сервере
    if call.data != 'None':
        logger.debug("User {} chose location {}", call.from_user.id, call.data)
        bot.set_state(call.from_user.id, UserParamState.check_in, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['location'] = call.data

        min = date.today() + timedelta(days=1)
        max = date.today() + timedelta(days=365)
        calendar, step = DetailedTelegramCalendar(min_date=min, max_date=max, locale='ru').build()
        bot.send_message(call.from_user.id, 'Введите дату заселения \U0001F4C5')
        bot.send_message(call.from_user.id, f'Выберите {LSTEP[step]}', reply_markup=calendar)

    else:
        bot.send_message(call.message.chat.id, 'Введите название локации')
        logger.debug("User {} cancelled search in chosen location", call.from_user.id)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c: CallbackQuery):
    # Обработчик ввода дат заселения и отъезда
    if bot.get_state(c.from_user.id) == UserParamState.check_in:
        min = date.today() + timedelta(days=1)
        max = date.today() + timedelta(days=365)

    else:
        with bot.retrieve_data(c.from_user.id) as data:
            min = data['check_in'] + timedelta(days=1)
            max = data['check_in'] + timedelta(days=28)

    result, key, step = DetailedTelegramCalendar(min_date=min, max_date=max, locale='ru').process(c.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              c.message.chat.id,
                              c.message.message_id)
        if bot.get_state(c.from_user.id) == UserParamState.check_in:
            logger.debug("User {} input check-in date: {}", c.from_user.id, result)
            with bot.retrieve_data(c.from_user.id) as data:
                data['check_in'] = result

            bot.set_state(c.from_user.id, UserParamState.check_out)
            min = result + timedelta(days=1)
            max = result + timedelta(days=28)
            calendar, step = DetailedTelegramCalendar(min_date=min, max_date=max, locale='ru').build()
            bot.send_message(c.from_user.id, 'Введите дату отъезда' )
            bot.send_message(c.from_user.id, f'Выберите {LSTEP[step]}', reply_markup=calendar)

        elif bot.get_state(c.from_user.id) == UserParamState.check_out:
            logger.debug("User {} input check-out date: {}", c.from_user.id, result)
            with bot.retrieve_data(c.from_user.id) as data:
                data['check_out'] = result
            bot.set_state(c.from_user.id, UserParamState.guests_amt)
            bot.send_message(c.from_user.id, 'Введите количество гостей', reply_markup=guests_amt_choice())


@bot.message_handler(state=UserParamState.guests_amt)
def get_guests_amt(message: Message) -> None:
    # Обработчик количества гостей, введенного пользователем
    logger.debug("User {} input guests amount: {}", message.from_user.id, message.text)
    if message.text.isdigit():
        if int(message.text) > 10 or int(message.text) == 0:
            bot.send_message(message.from_user.id, 'Количество гостей может быть от 1 до 10\nПовторите ввод')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['guests_amt'] = message.text
            bot.send_message(message.from_user.id, 'Введите нужное количество результатов',
                             reply_markup=results_amt_choice())
            bot.set_state(message.from_user.id, UserParamState.results_amt, message.chat.id)
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести целое число')


@bot.message_handler(state=UserParamState.results_amt)
def get_results_amt(message: Message) -> None:
    # Обработчик количества результатов, заданных пользователем
    logger.debug("User {} input results amount: {}", message.from_user.id, message.text)
    if message.text.isdigit():
        if int(message.text) > 25 or int(message.text) == 0:
            bot.send_message(message.from_user.id, 'Количество результатов может быть от 1 до 25\nПовторите ввод')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['results_amt'] = message.text
            bot.send_message(message.from_user.id, 'Нужно ли загружать фото отелей?', reply_markup=show_pics())
            bot.set_state(message.from_user.id, UserParamState.show_pics, message.chat.id)
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести целое число')


@bot.message_handler(state=UserParamState.show_pics)
def get_pics(message: Message) -> None:
    # Обработчик ответа пользователя - требуется ли загрузка фото отелей
    logger.debug("User {} chose {} in 'show pics' step", message.from_user.id, message.text)
    if message.text == 'Да':
        bot.send_message(message.from_user.id, 'Введите количество фотографий', reply_markup=pics_amt_choice() )
        bot.set_state(message.from_user.id, UserParamState.pics_amt, message.chat.id)
    elif message.text == 'Нет':
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['pics_amt'] = 0
            command = data['command']
        if command == '/bestdeal':
            bot.set_state(message.from_user.id, UserParamState.dist_max, message.chat.id)
            bot.send_message(message.from_user.id, 'Введите максимально допустимое расстояние до центра')
        else:
            get_results(message.from_user.id)
    else:
        bot.send_message(message.from_user.id, 'Сделайте выбор, нажав на кнопку', reply_markup=show_pics())


@bot.message_handler(state=UserParamState.pics_amt)
def get_pics_amt(message: Message) -> None:
    # Обработчик введенного пользователем количества требуемых фото каждого отеля
    logger.debug("User {} input pics amount: {}", message.from_user.id, message.text)
    if message.text.isdigit():
        if int(message.text) > 6 or int(message.text) < 1:
            bot.send_message(message.from_user.id, 'Количество фото может быть от 1 до 6\nПовторите ввод')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['pics_amt'] = int(message.text)
                command = data['command']
            if data['command'] == '/bestdeal':
                bot.set_state(message.from_user.id, UserParamState.dist_max, message.chat.id)
                bot.send_message(message.from_user.id, 'Введите максимально допустимое расстояние до центра')
            else:
                get_results(message.from_user.id)
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести целое число от 1 до 6')


@bot.message_handler(state=UserParamState.dist_max)
def get_dist_max(message: Message) -> None:
    # Обработчик введенного пользователем максимально допустимого расстояния до центра
    logger.debug("User {} input distance to center: {}", message.from_user.id, message.text)
    if message.text.isdigit():
        if int(message.text) > 30 or int(message.text) < 1:
            bot.send_message(message.from_user.id,
                             'Введите число в диапазоне от 1 до 30, большее минимальной границы')
        else:
            bot.set_state(message.from_user.id, UserParamState.price_max, message.chat.id)
            bot.send_message(message.from_user.id, 'Введите максимально допустимую стоимость (USD)')
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['dist_max'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Введите число от 1 до 30')


@bot.message_handler(state=UserParamState.price_max)
def get_price_min(message: Message) -> None:
    # Обработчик введенной пользователем максимально допустимой цены
    logger.debug("User {} input maximum price: {}", message.from_user.id, message.text)
    if message.text.isdigit():
        if int(message.text) > 0:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['price_max'] = message.text
            get_results(message.from_user.id)
        else:
            bot.send_message(message.from_user.id, 'Введите число больше нуля')
    else:
        bot.send_message(message.from_user.id, 'Введите число')


def get_results(user_id: int) -> None:
    """
    Функция инициирует поисковый запрос на основании введенных пользователем параметров
    и производит вывод результатов в телеграм-чат
    :param user_id: user-ID пользователя
    :return: None
    """
    bot.send_message(user_id, 'Производится поиск отелей   \U0000231B')
    try:
        results = find_hotels(user_id)
        res_amt = len(results)
        logger.debug("{} results found", res_amt)
        if res_amt != 0:
            bot.send_message(user_id, f'Найдено отелей: {res_amt}')
            for hotel in results:
                bot.send_message(user_id, hotel.info, disable_web_page_preview=True)
                if len(hotel.pics_list) != 0:
                    image_lst = [InputMediaPhoto(image) for image in hotel.pics_list]
                    bot.send_media_group(user_id, image_lst)
            db_write(user_id=user_id, search_results=results)
        else:
            bot.send_message(user_id, "Подходящих отелей не найдено")
        bot.delete_state(user_id)
        logger.debug("User {} state={}", user_id, bot.get_state(user_id))

    except ApiBadResponse as ex:
        bot.send_message(user_id, 'Возникла ошибка на сервере. Повторите запрос.')
        logger.error("{}", ex)
        bot.delete_state(user_id)
