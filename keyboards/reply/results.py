from telebot.types import ReplyKeyboardMarkup


def results_amt_choice() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, True)
    keyboard.row('5', '10', '15', '25')
    return keyboard
