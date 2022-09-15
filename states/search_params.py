from telebot.handler_backends import State, StatesGroup


class UserParamState(StatesGroup):
    location = State()
    check_in = State()
    check_out = State()
    guests_amt = State()
    results_amt = State()
    show_pics = State()
    pics_amt = State()
    dist_max = State()
    price_max = State()
    history = State()
