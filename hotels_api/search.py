import re
from hotels_api.api_request import api_request
from loader import bot


def city_id(city: str) -> list:
    """
    Функция возвращает варианты локаций в базе Hotels.com на основании ввденного имени
    :param city: (str) Название города
    :return: (list) список найденных локаций по запросу
    """
    city = city.lower()
    api_url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    querystring = {'query': city, 'locale': 'ru_RU', 'currency': 'USD'}
    result = api_request(api_url=api_url, querystring=querystring)
    locations = result['suggestions'][0]['entities']
    found_loc = list()
    for item in locations:
        # if item['type'] == 'CITY' and (item['name'].lower() in city):
        if item['type'] == 'CITY':
            # Очистка строки от тегов
            caption = re.sub(r'<.*?(>)|(>[.,])', '', item['caption'])
            caption = re.sub(r'<.*?(>)|(>[.,])', '', caption)
            caption = re.sub(r'<.*?(>)|(>[.,])', '', caption)
            caption = re.sub(r'<.*?(>)|(>[.,])', '', caption)
            found_loc.append([int(item['destinationId']), caption])
    return found_loc


class Hotel:
    """
    Класс Отель. Элемент результатов поиска.

    Args:
        id (str): передается id отеля
        info (str): передается найденная информация об отеле
        pics_amt (str): передается количество фотографий для вывода

    Attributes:
        pics_list (list): список фотографий отеля
    """
    def __init__(self, id: str, info: str, pics_amt: int):
        self.id = id
        self.info = info
        self.pics_list = list()
        if pics_amt != 0:
            self.get_pics(pics_amt)

    def get_pics(self, pics_amt: int) -> None:
        """
        Метод создает список фотографий при инициализации элемента класса Отель.
        Если запрошенное число фотографий = 0, то список остается пустым.
        :param pics_amt: (int) необходимое количество фотографий
        """
        api_url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
        querystring = {'id': str(self.id)}
        result = api_request(api_url=api_url, querystring=querystring)

        counter = 0
        for elem in result['hotelImages']:
            pic_link = elem['baseUrl'].replace('{size}', 'z')
            self.pics_list.append(pic_link)
            counter +=1
            if counter == pics_amt:
                    break


def find_hotels(user_id: int) -> list:
    """
    Функция выполняет поисковый запрос в соответствии с заданными параметрами
    и возвращает список результатов
    :return: None
    """
    dist_max = 0
    with bot.retrieve_data(user_id) as data:

        querystring = {'destinationId': data['location'], 'pageNumber': '1',
                       'pageSize': data['results_amt'],   'checkIn': data['check_in'],
                       'checkOut': data['check_out'],     'adults1': data['guests_amt'],
                       'locale': 'en_US',                 'currency': 'USD'}
        if data['command'] == '/lowprice':
            querystring['sortOrder'] = 'PRICE'
        elif data['command'] == '/highprice':
            querystring['sortOrder'] = 'PRICE_HIGHEST_FIRST'
        elif data['command'] == '/bestdeal':
            querystring['sortOrder'] = 'DISTANCE_FROM_LANDMARK'
            querystring['priceMin'] = '0'
            querystring['priceMax'] = data['price_max']
            dist_max = data['dist_max']
        pics_amt = data['pics_amt']

    api_url = 'https://hotels4.p.rapidapi.com/properties/list'
    result = api_request(api_url=api_url, querystring=querystring)
    if not result:
        raise BaseException

    loc_name = result['data']['body'].get('header')
    hotels_list = result['data']['body']['searchResults']['results']
    if len(hotels_list) == 0:
        raise BaseException

    search_results = list()
    for elem in hotels_list:
        if dist_max != 0:
            dist = elem["landmarks"][0]["distance"].split()[0]
            dist = re.sub(r',', '.', dist)
            dist = float(dist)
            if dist > float(dist_max):
                break
        hotel_id = elem.get("id")
        info = f'ID отеля: {elem.get("id")}\n' \
            f'Название отеля: {elem.get("name")}\n' \
            f'Адрес отеля: {elem["address"].get("locality")}, {elem["address"].get("streetAddress")}\n' \
            f'Расстояние до центра: {" ".join([elem["landmarks"][0]["label"], elem["landmarks"][0]["distance"]])}\n' \
            f'Цена за ночь: {elem["ratePlan"]["price"].get("current")}\n' \
            f'Итоговая стоимость с налогами и сборами: {elem["ratePlan"]["price"].get("fullyBundledPricePerStay")}\n' \
            f'Страница отеля:\n https://www.hotels.com/ho{elem.get("id")}'
        info = re.sub(r'&nbsp;', ' ', info)
        next_hotel = Hotel(hotel_id, info, pics_amt)
        search_results.append(next_hotel)

    return search_results
