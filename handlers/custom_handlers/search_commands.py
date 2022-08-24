from loader import bot
from states.search_params import UserParamState
from telebot.types import Message, InputMediaPhoto
from keyboards.inline.locations_list import location_choice
from keyboards.reply.guests import guests_amt_choice
from keyboards.reply.results import results_amt_choice
from keyboards.reply.photos import show_pics, pics_amt_choice
from datetime import datetime
from hotels_api.search import city_id, find_hotels



@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def lowprice(message: Message) -> None:
    bot.set_state(message.from_user.id, UserParamState.location, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text
    bot.send_message(message.from_user.id, f'Введите название локации')


@bot.message_handler(state=UserParamState.location)
def get_location(message: Message) -> None:
    result_city_id = city_id(message.text)
    if not result_city_id:
        bot.send_message(message.chat.id, 'Город с таким названием не найден в базе. Попробуйте изменить запрос.')
    else:
        bot.send_message(message.chat.id, text=f'Найдены следующие локации, сделайте выбор:', reply_markup=location_choice(result_city_id))


@bot.callback_query_handler(func=lambda call: True)
def location_select(call):
    if call.data != 'None':
        bot.set_state(call.from_user.id, UserParamState.check_in, call.message.chat.id)
        bot.send_message(call.message.chat.id, f'Введите дату заселения (yyyy-mm-dd)')
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['location'] = call.data
    else:
        bot.send_message(call.message.chat.id, 'Введите название локации')


@bot.message_handler(state=UserParamState.check_in)
def get_check_in(message: Message) -> None:
    try:
        check_in_date = datetime.date(datetime.strptime(message.text, '%Y-%m-%d'))
        if check_in_date > datetime.date(datetime.today()):
            bot.set_state(message.from_user.id, UserParamState.check_out, message.chat.id)
            bot.send_message(message.from_user.id, f'Введите дату отъезда (yyyy-mm-dd)')
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['check_in'] = check_in_date
        else:
            bot.send_message(message.from_user.id, 'Дата заезда не может быть раньше завтрашнего дня!\n Повторите ввод.')
    except ValueError:
        bot.send_message(message.from_user.id, 'Необходимо ввести дату в формате   yyyy-mm-dd')


@bot.message_handler(state=UserParamState.check_out)
def get_check_out(message: Message) -> None:
    try:
        check_out_date = datetime.date(datetime.strptime(message.text, '%Y-%m-%d'))
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if check_out_date > data['check_in']:
                bot.set_state(message.from_user.id, UserParamState.guests_amt, message.chat.id)
                bot.send_message(message.from_user.id,
                                 f'Введите количество гостей',
                                 reply_markup=guests_amt_choice())
                data['check_out'] = check_out_date
            else:
                bot.send_message(message.from_user.id, 'Дата отъезда должна быть больше даты заезда\n Повторите ввод.')
    except ValueError:
        bot.send_message(message.from_user.id, 'Необходимо ввести дату в формате   yyyy-mm-dd')


@bot.message_handler(state=UserParamState.guests_amt)
def get_guests_amt(message: Message) -> None:
    if message.text.isdigit():
        if int(message.text) > 10 or int(message.text) == 0:
            bot.send_message(message.from_user.id, 'Количество гостей может быть от 1 до 10\nПовторите ввод')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['guests_amt'] = message.text
            bot.send_message(message.from_user.id, 'Введите нужное количество результатов', reply_markup=results_amt_choice())
            bot.set_state(message.from_user.id, UserParamState.results_amt, message.chat.id)
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести целое число')


@bot.message_handler(state=UserParamState.results_amt)
def get_results_amt(message: Message) -> None:
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
        bot.send_message(message.from_user.id, 'Необходимо ввести целое число от 1 до 5')


@bot.message_handler(state=UserParamState.dist_max)
def get_dist_max(message: Message) -> None:
    if message.text.isdigit():
        if int(message.text) > 30 or int(message.text) < 1:
            bot.send_message(message.from_user.id, 'Введите число в диапазоне от 1 до 30, большее минимальной границы')
        else:
            bot.set_state(message.from_user.id, UserParamState.price_max, message.chat.id)
            bot.send_message(message.from_user.id, 'Введите максимально допустимую стоимость')
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['dist_max'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Введите число от 1 до 30')


@bot.message_handler(state=UserParamState.price_max)
def get_price_min(message: Message) -> None:
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
    bot.send_message(user_id, 'Производится поиск отелей...')
    try:
        results = find_hotels(user_id)
        if len(results) == 0:
            raise BaseException
        for hotel in results:
            bot.send_message(user_id, hotel.info, disable_web_page_preview=True)
            if len(hotel.pics_list) != 0:
                image_lst = [InputMediaPhoto(image) for image in hotel.pics_list]
                bot.send_media_group(user_id, image_lst)
    except BaseException:
        bot.send_message(user_id, 'Не удалось найти подходящие отели\nПовторите или измените запрос')