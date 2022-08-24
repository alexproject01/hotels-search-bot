from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def show_pics() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, True)
    keyboard.row('Да', 'Нет')
    return keyboard

def pics_amt_choice() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, True, input_field_placeholder='Количество фото: 1-6')
    keyboard.row('2', '4', '6')
    return keyboard