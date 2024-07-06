import psycopg2
import requests
import os


# преобразовывает код валюты в символ (RUR -> ₽)
def re_currency(cur):
    dictionary_json = requests.get("https://api.hh.ru/dictionaries").json()
    for q in dictionary_json["currency"]:
        if q["code"] == cur:
            return str(q["abbr"])



def create_connection():
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("Переменная окружения DATABASE_URL не определена!")
        conn = psycopg2.connect(database_url)
        print("соединение с hh_db прошло успешно")
        return conn

    except Exception as e:
        print(f"Ошибка при подключении к PostgreSQL: {e}")
        return None


def create_table(conn, cursor):
    create_table_query = """
        CREATE TABLE IF NOT EXISTS vacancies (
            id SERIAL PRIMARY KEY,
            url VARCHAR(100),
            name VARCHAR(200),
            salary_from INTEGER,
            schedule VARCHAR(20),
            city VARCHAR(50),
            company VARCHAR(200),
            salary_to INTEGER)
    """
    cursor.execute(create_table_query)
    conn.commit()
    print("таблица создана")


def drop_table(conn, cursor):
    cursor.execute("DROP TABLE IF EXISTS vacancies")
    conn.commit()
    print("таблица удалена")


# ф-я с запросом в api
def get_vacancies(data_in, page):
    url = f"https://api.hh.ru/vacancies?per_page=50&only_with_salary=true&page={page}&text={data_in['name_in']}&search_field=name"  # per_page - tyt kosyak   paginatsiya = 2000 default t.e.
    if data_in["salary_in"]:
        url += "&salary=" + data_in["salary_in"]
    for w in range(5):
        if data_in["schedule"][w]["state"]:
            url += "&schedule=" + data_in["schedule"][w]["id"] 
    if data_in["area_in"]:
        for a in data_in["area_in"]:
            url += "&area=" + a["id"]
    print(url)
    response = requests.get(url)
    if str(response.status_code) != "200":
        print(response.json())
        return None
    return response.json()


def parse_vacancies(conn, cursor, data_in):
    page = 0
    while page <= 39:  # учтена пагинация - ограничение в 2000 выданных вакансий за раз
        try:
            data = get_vacancies(data_in, page)
            if data is None:
                print("vsyo break")
                break
            for item in data['items']:
                url = str(item['alternate_url'])
                name = str(item['name'])
                if item["salary"]["from"] is None:
                    continue
                if item["salary"]["to"] is None:
                    continue
                salary_from = int(item["salary"]["from"])
                salary_to = int(item["salary"]["to"])
                if re_currency(str((item["salary"]["currency"]))) != "₽":
                    continue
                schedule = str(item["schedule"]["name"])
                city = str(item["area"]["name"])
                company = str(item['employer']['name']).lower()
                insert_query = """
                    INSERT INTO vacancies (url, name, salary_from, schedule, city, company, salary_to) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """
                cursor.execute(insert_query, (url, name.lower(), salary_from, schedule, city, company, salary_to))
                conn.commit()
            if page < data['pages'] - 2:  # ?
                page += 1
            else:
                break
        except requests.HTTPError as e:
            print(e)
            break
        except psycopg2.Error as e:
            print(e)
        except Exception as e:
            print(e)
            break
    print("Парсинг завершен. Данные сохранены в базе данных PostgreSQL.")


def remove_duplicates(conn, cursor):
    delete_duplicates_query = """
            DELETE FROM vacancies
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM vacancies
                GROUP BY url
            )
        """
    cursor.execute(delete_duplicates_query)
    conn.commit()
    print("Дубликаты в таблице 'vacancies' успешно удалены.")
