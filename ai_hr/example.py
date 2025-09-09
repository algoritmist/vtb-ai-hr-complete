from analyzer import analyze_vacancy_vs_resume

# Сравнение вакансии и резюме по путям к файлам
result = analyze_vacancy_vs_resume(
    vacancy_file="/home/user/vacancies/Вакансия_ИТ_специалист.docx",
    resume_file="/home/user/resumes/Резюме_Иванов.docx"
)

# Вывод результата
import json
print(json.dumps(result, ensure_ascii=False, indent=2))


from analyzer import (
    parse_text_to_dict,
    clean_and_format_dict,
    parse_vacancy_from_json,
    InterviewAnalyzer
)

# текст вакансии как строка 
vacancy_text = """
Название: Инженер Python
Обязанности (для публикации): Разработка backend на Python; Работа с Docker и CI/CD.
Требования (для публикации): Опыт от 3 лет; Знание FastAPI; Docker.
Требуемый опыт работы: от 3 лет
"""

# Шаг 1: Парсим текст в словарь
vacancy_dict_raw = parse_text_to_dict(vacancy_text)

# Шаг 2: Очищаем
vacancy_dict_clean = clean_and_format_dict(vacancy_dict_raw)

# Шаг 3: Преобразуем в унифицированный формат
vacancy_structured = parse_vacancy_from_json(vacancy_dict_clean)

# Шаг 4: Текст резюме (может быть из файла или строки)
resume_text = """
Опыт работы: 4 года Python-разработчиком. Использовал FastAPI, Docker, GitLab CI.
Образование: МГТУ им. Баумана.
Навыки: Python, SQL, Docker, Linux, Git.
"""

# Шаг 5: Анализ
analyzer = InterviewAnalyzer()
result = analyzer.analyze(
    resume_input=resume_text,           # str → анализируется как резюме
    vacancy=vacancy_structured,         # структурированная вакансия
    return_features=True
)

# Вывод
import json
print(json.dumps(result, ensure_ascii=False, indent=2))