from datetime import datetime, timedelta

from candidate.schemas import CandidateSchema
from candidate.views import candidate_create
from contract.schemas import InterviewResultSchema
from contract.views import interview_assign_report
from minio import Minio
from minio.error import S3Error
from recruiter.schemas import InterviewSchema, RecruiterSchema, VacancySchema
from recruiter.views import interview_create, recruiter_create, vacancy_create


def upload_minio():
    client = Minio(
        "localhost:9000",
        access_key="root",
        secret_key="12345678",
        secure=False,
    )

    resume_files = [
        "resources/bussiness_analyst_1.pdf",
        "resources/bussiness_analyst_2.pdf",
        "resources/it_lead_1.pdf",
        "resources/it_lead_2.pdf",
    ]

    vacancy_files = [
        "resources/bussiness_analyst_description.pdf",
        "resources/it_lead_description.pdf",
    ]

    bucket1_name = "resume"
    bucket2_name = "vacancies"

    found = client.bucket_exists(bucket1_name)
    if not found:
        client.make_bucket(bucket1_name)
    for source_file in resume_files:
        destination_file = source_file.split("/")[-1]
        client.fput_object(bucket1_name, destination_file, source_file)

    found = client.bucket_exists(bucket2_name)
    if not found:
        client.make_bucket(bucket2_name)
    for source_file in vacancy_files:
        destination_file = source_file.split("/")[-1]
        client.fput_object(bucket2_name, destination_file, source_file)


def populate():
    upload_minio()
    it_specialist_candidate_1 = CandidateSchema(
        first_name="Иван",
        second_name="Иванович",
        last_name="Иванов",
        login="ivanov_ii",
        password="secure_password_123",
        resume="it_lead_1.pdf",
    )

    it_specialist_candidate_2 = CandidateSchema(
        first_name="Дмитрий",
        second_name="Андреевич",
        last_name="Кузнецов",
        login="kuznetson_da",
        password="just_password_135",
        resume="it_lead_2.pdf",
    )

    business_analyst_candidate_1 = CandidateSchema(
        first_name="Анна",
        second_name="Александровна",
        last_name="Петрова",
        login="petrova_aa",
        password="strong_pass_456",
        resume="bussiness_analyst_1.pdf",
    )

    business_analyst_candidate_2 = CandidateSchema(
        first_name="Алексей",
        second_name="Сергеевич",
        last_name="Смирнов",
        login="smirnov_as",
        password="safe_pwd_789",
        resume="bussiness_analyst_2.pdf",
    )

    it_specialist_id_1 = candidate_create(it_specialist_candidate_1)
    it_specialist_id_2 = candidate_create(it_specialist_candidate_2)
    finance_specialist_id_1 = candidate_create(business_analyst_candidate_1)
    finance_specialist_id_2 = candidate_create(business_analyst_candidate_2)

    recruiter_it_candidate = RecruiterSchema(
        first_name="Елена",
        second_name="Викторовна",
        last_name="Семёнова",
        login="semenova_ev",
        password="hr_recruiter_123",
        department="Отдел подбора персонала ИТ-компании",
    )

    recruiter_finance_candidate = RecruiterSchema(
        first_name="Дмитрий",
        second_name="Андреевич",
        last_name="Королев",
        login="korolev_da",
        password="finance_hr_456",
        department="Финансовое подразделение крупной корпорации",
    )

    recruiter_it_id = recruiter_create(recruiter_it_candidate)
    recruiter_finance_id = recruiter_create(recruiter_finance_candidate)

    vacancy_it_lead = VacancySchema(
        recruiter_id=recruiter_it_id,
        description="Требуется опытный специалист с глубокими техническими компетенциями.",
        position="Ведущий IT-специалист",
        keywords=",".join(
            [
                "Монтаж и демонтаж серверного оборудования",
                "Настройка сетевых устройств",
                "Первичная настройка серверов (BIOS/BMC/RAID)",
                "Решение технических инцидентов x86-серверов",
                "Обслуживание серверных помещений",
                "Работа с системами учёта CMDB и DCIM",
                "Организация подрядных работ в ЦОД",
                "Базовая диагностика аппаратуры",
                "Понимание сетей LAN/SAN",
                "Опыт работы с кабельными системами (медные/оптические)",
                "Управление инфраструктурой ЦОД",
                "Основы архитектуры серверов x86",
                "Высокий уровень владения MS Office (Excel, Word, Visio)",
                "Устная и письменная коммуникабельность",
                "Аккуратность и ответственность",
                "Инициативность и исполнительность",
            ]
        ),
        bucket_name="vacancies",
        filename="it_lead_description.pdf",
        expires_at=(datetime.now() + timedelta(days=30)),
    )

    vacancy_business_analyst = VacancySchema(
        recruiter_id=recruiter_finance_id,
        description="Необходимо проведение глубокого анализа бизнес-требований и создание технической документации.",
        position="Бизнес-аналитик",
        keywords="".join(
            [
                "Управление комплексом систем предотвращения мошенничества",
                "Формулирование предложений по оптимизации антифрод-решений",
                "Участие в инициативах развития финансовых платформ",
                "Анализ и подготовка бизнес-требований",
                "Постановка задач разработчикам",
                "Создание тестовых кейсов и проведение функционального тестирования",
                "Практический опыт работы с ПО антифрод и ПОД/ФТ",
                "Операции с корпоративными картами и ДБО",
                "Понимание механизмов учета и планирования платежей ЮЛ",
                "Аналитика клиентского пути юридических лиц",
                "Анализ сценариев мошенничества и защита от угроз",
                "Разработка качественной проектной документации",
                "Работа с реляционными базами данных и SQL-запросы",
                "Понимание архитектурных подходов к созданию приложений",
                "Владение стандартами и протоколами платежных систем",
                "Продвинутый уровень владения пакетами MS Office (Word, Excel, PowerPoint)",
            ],
        ),
        bucket_name="vacancies",
        filename="bussiness_analyst_description.pdf",
        expires_at=(datetime.now() + timedelta(days=60)),
    )

    it_vacancy_id = vacancy_create(vacancy_it_lead)
    finance_vacancy_id = vacancy_create(vacancy_business_analyst)

    interview_it_specialist_1 = InterviewSchema(
        id="b74abe2f-ff91-4df6-9894-7b37591f37bd",
        candidate_id=it_specialist_id_1,
        vacancy_id=it_vacancy_id,
        start_time=(datetime.now() + timedelta(days=15)),
        description="Интервью на позицию ведущего IT-специалиста",
        conference_id="conf-it-specialist-2025-03-15",
    )

    interview_it_specialist_2 = InterviewSchema(
        candidate_id=it_specialist_id_2,
        vacancy_id=it_vacancy_id,
        start_time=(datetime.now() + timedelta(days=15)),
        description="Интервью на позицию ведущего IT-специалиста",
        conference_id="conf-it-specialist-2025-03-16",
    )

    interview_business_analyst_1 = InterviewSchema(
        candidate_id=finance_specialist_id_1,
        vacancy_id=finance_vacancy_id,
        start_time=(datetime.now() + timedelta(days=15)),
        description="Интервью на должность бизнес-аналитика",
        conference_id="conf-business-analyst-2025-03-20",
    )

    interview_business_analyst_2 = InterviewSchema(
        candidate_id=finance_specialist_id_2,
        vacancy_id=finance_vacancy_id,
        start_time=(datetime.now() + timedelta(days=15)),
        description="Интервью на должность бизнес-аналитика",
        conference_id="conf-business-analyst-2025-03-21",
    )

    interview_it_specialist_1_id = interview_create(interview_it_specialist_1)
    print(interview_it_specialist_1)
    interview_it_specialist_2_id = interview_create(interview_it_specialist_2)
    interview_business_analyst_1_id = interview_create(
        interview_business_analyst_1
    )
    interview_business_analyst_2_id = interview_create(
        interview_business_analyst_2
    )

    interview_assign_report(
        id=interview_it_specialist_1_id,
        interview_result=InterviewResultSchema(
            interview_uuid=interview_it_specialist_1_id,
            analysis_result='{"total_match_percent": 0.95}',
        ),
    )
    interview_assign_report(
        id=interview_it_specialist_2_id,
        interview_result=InterviewResultSchema(
            interview_uuid=interview_it_specialist_1_id,
            analysis_result='{"total_match_percent": 0.2}',
        ),
    )
    interview_assign_report(
        id=interview_business_analyst_1_id,
        interview_result=InterviewResultSchema(
            interview_uuid=interview_business_analyst_1_id,
            analysis_result='{"total_match_percent": 0.8}',
        ),
    )
    interview_assign_report(
        id=interview_business_analyst_2_id,
        interview_result=InterviewResultSchema(
            interview_uuid=interview_business_analyst_2_id,
            analysis_result='{"total_match_percent": 0.4}',
        ),
    )
