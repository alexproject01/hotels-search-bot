from telebot.types import ReplyKeyboardMarkup


def history_next() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, True)
    keyboard.row('Да', 'Нет')
    return keyboard
