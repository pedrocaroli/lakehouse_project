from api_request import fetch_data
import psycopg2 

def connect_to_db():
    print('Inciando conexão com o database...')
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname= 'db_projeto_1',
            user= 'pedrocaroli',
            password= 'Btrab0130##'

        )
        print('Conexão criada com sucesso')
        print(conn)
        return conn
    except psycopg2.errors as e:
        print(f'Erro: {e}')