import datetime
import os
import requests
from dotenv import load_dotenv
from terminaltables import SingleTable


def fetch_hh_vacancies(text, area, date_from, token = None):
    vacancies = []
    page = 0
    pages_number = 1
    hh_api_url = "https://api.hh.ru/vacancies"
    params = {
      "text": text,
      "area": area,
      "date_from": date_from,
    }
    while page < pages_number:
        params["page"] = page
        page_response = requests.get(hh_api_url, params)
        page_response.raise_for_status()
        response = page_response.json() 
        pages_number = response["pages"]
        page += 1
        vacancies_on_page = response
        vacancies += vacancies_on_page["items"]
        found = vacancies_on_page["found"]
    return vacancies, found


def fetch_sj_vacancies(keyword, town, date_published_from, token = None):
    vacancies_on_page_count = 20
    vacancies = []
    page = 0
    pages_number = 1
    sj_api_url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": token,
    }
    params = {
        "town": town,
        "keyword": keyword,
        "catalogues": 48,
        "date_published_from": date_published_from,
        "count": vacancies_on_page_count,
    }
    while page < pages_number:
        params["page"] = page
        page_response = requests.get(sj_api_url, params=params, headers=headers)
        page_response.raise_for_status()
        vacancies_on_page = page_response.json()
        found = vacancies_on_page["total"]
        pages_number = found // vacancies_on_page_count + 1
        page += 1
        vacancies += vacancies_on_page["objects"]
    return vacancies, found


def get_vacancies_statistic(func_fetch_vacancies, func_predict_rub_salary, job_area, vacancies_period, token=None):
    job_statistics = {}
    popular_prog_languages = [
        "Java",
        "Python",
        "Ruby",
        "PHP",
        "C++",
        "C#",
        "Go",
        "Scala",
        "Swift",
    ]
    for popular_prog_language in popular_prog_languages:
        salary_sum = 0
        vacancies_processed = 0
        job_specialization = f"Программист {popular_prog_language}"
        vacancies, found = func_fetch_vacancies(job_specialization, job_area, vacancies_period, token)
        for vacancy in vacancies:
            rub_salary = func_predict_rub_salary(vacancy)
            try:
                if rub_salary:
                    salary_sum += rub_salary
                    vacancies_processed += 1
                    average_salary = int(salary_sum / vacancies_processed)
                else:
                    not rub_salary
            except ZeroDivisionError:
                average_salary = 0
        job_statistics[popular_prog_language] = {
            "vacancies_found": found,
            "average_salary": average_salary,
            "vacancies_processed": vacancies_processed,
        }
    return job_statistics



def predict_rub_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) // 2
    if salary_from and not salary_to:
        return int(salary_from * 1.2)
    if not salary_from and salary_to:
        return int(salary_to * 0.8)


def predict_rub_salary_hh(vacancy):
    salary = vacancy["salary"]
    if salary and salary["currency"] == "RUR":
        return predict_rub_salary(salary["from"], salary["to"])


def predict_rub_salary_sj(vacancy):
    if vacancy["currency"] == "rub":
        return predict_rub_salary(vacancy["payment_from"], vacancy["payment_to"])


def get_vacancies_statictic_in_table(title, statictics):
     profession_statistic = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]
    for prog_lang, statictic in statictics.items():
         profession_statistic.append(
           [
               prog_lang,
               statictic["vacancies_found"],
               statictic["vacancies_processed"],
               statictic["average_salary"],
          ]
        )
    table_instance = SingleTable( profession_statistic, title)
    return table_instance.table

    
def main():
    load_dotenv()
    sj_api_key = os.environ["SUPERJOB_TOKEN"]
    sj_job_area = 4
    hh_job_area = 1
    vacancies_search_days = 30
    hh_title = "HeadHunter Moscow"
    sj_title = "SuperJob Moscow"
    date_search_from = (datetime.datetime.now() - datetime.timedelta(days=vacancies_search_days)).date()
    hh_statistic = get_vacancies_statistic(fetch_hh_vacancies, predict_rub_salary_hh, hh_job_area, date_search_from)
    sj_statistic = get_vacancies_statistic(fetch_sj_vacancies, predict_rub_salary_sj, sj_job_area, date_search_from, sj_api_key)
    print(get_vacancies_statictic_in_table(hh_title, hh_statistic))
    print(get_vacancies_statictic_in_table(sj_title, sj_statistic))


if __name__ == "__main__":
    main()
