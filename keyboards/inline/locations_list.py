from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def location_choice(loc_list: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    for item in loc_list:
        button = InlineKeyboardButton(text=f'{item[1]} (id {item[0]})', callback_data=item[0])
        keyboard.add(button)
    button = InlineKeyboardButton(text='Отмена', callback_data='None')
    keyboard.add(button)
    return keyboard
