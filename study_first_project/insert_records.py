from study_first_project.api_request import fetch_data
import psycopg2 as psycopg2
import pandas as pd
from psycopg2.extras import execute_values

def connect_to_db():
    print('Inciando conexão com o database...')
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname= 'db_projeto_1',
            user= 'pedrocaroli',
            password= 'Btrb0130##'

        )
        print('Conexão criada com sucesso')
        print(conn)
        return conn
    except psycopg2.errors as e:
        print(f'Erro: {e}')

def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
                    CREATE SCHEMA IF NOT EXISTS dev;
                    CREATE TABLE IF NOT EXISTS dev.raw_cotacao_data (
                    code TEXT,
                    codein TEXT,
                    name TEXT,
                    high FLOAT, 
                    low FLOAT,
                    create_date TIMESTAMP,
                    timestamp BIGINT
                    );
                    """)
        conn.commit()
        print('Table Created')
    except psycopg2.errors as e:
        print(f'Erro: {e}')



def insert_values(conn,data):
    try:
        df = pd.DataFrame(data)
        df['timestamp_ajust'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        colunas = ['code', 'codein', 'name', 'high', 'low', 'create_date','timestamp']
        values = []
        for item in data:
            linha = [item.get(col, None) for col in colunas]
            values.append(tuple(linha))
        
        cursor = conn.cursor()
        query = """
                    INSERT INTO dev.raw_cotacao_data (
                    code,
                    codein,
                    name,
                    high, 
                    low,
                    create_date,
                    timestamp
                    ) VALUES %s
    """
        execute_values(cursor, query, values)
        conn.commit()
        print("Dados inseridos com sucesso.")
    
    except psycopg2.errors as e:
        print(f'Erro: {e}')
    
def main():
    try:
        data = fetch_data()
        conn = connect_to_db()
        create_table(conn)
        insert_values(conn,data)
    except Exception as e:
        print(f'Erro: {e}')
    finally:
        if 'conn' in locals():
            conn.close()
            print('Databse connection closed')

main()