import json
import requests
from config_data import config


def api_request(api_url, querystring):
    for _ in range(3):
        response = requests.get(url=api_url,
                                params=querystring,
                                headers={'X-RapidAPI-Key': config.RAPID_API_KEY,
                                         'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'
                                         },
                                timeout=10)
        if response.status_code == requests.codes.ok:
            result = json.loads(response.text)
            return result
    return None
