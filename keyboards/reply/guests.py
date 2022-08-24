from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def guests_amt_choice() -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(True, True, input_field_placeholder='Максимум: 10 человек')
    keyboard.row('1', '2', '3', '4', '5')

    return keyboard