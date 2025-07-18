import requests

def fetch_data():
    try:

        url = 'https://economia.awesomeapi.com.br/json/daily/USD-BRL/15'
        response = requests.get(url)
        response.raise_for_status()
        print("API rodou corretamente")
        return response.json()

    except:
        print('Ocorreu um erro na conexão da API')

##fetch_data()
