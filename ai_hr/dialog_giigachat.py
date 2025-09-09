from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from enum import Enum
from typing import List, Dict, Optional, Any
import json
import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GigaChatModel(Enum):
    """Доступные модели GigaChat"""
    LITE = 'GigaChat'
    PRO = 'GigaChat-Pro'
    PLUS = 'GigaChat-Plus'
    MAX = 'GigaChat-Max'


class HRAssistant:
    """Класс HR-ассистента на основе GigaChat API с поддержкой функций"""

    def __init__(self, api_key: str, model: GigaChatModel = GigaChatModel.LITE, vacancy: Optional[str] = None):
        """
        Инициализация HR-ассистента

        Args:
            api_key: API ключ для доступа к GigaChat (обязательно)
            model: выбранная модель
            vacancy: текст вакансии (опционально)
        """
        if not api_key:
            raise ValueError("api_key must be provided for HRAssistant")

        self.api_key = api_key
        self.model_name = model.value
        self.vacancy = vacancy
        self.dialog_active = True
        self.dialog_history: List[tuple] = []

        self.giga = GigaChat(
            credentials=self.api_key,
            model=self.model_name,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS"
        )

        self.messages: List[Dict] = []
        self.system_prompt = self._create_system_prompt()
        self.functions = self._define_functions()
        self._initialize_dialog()

    def _create_system_prompt(self) -> str:
        """Создание системного промпта на основе вакансии"""
        base_prompt = (
            "Ты AI HR банка ВТБ, для первичной проверки соответствия кандидата вакансии.\n"
            "Твоя задача задать кандидату от 3 до 10 вопросов по вакансии в зависимости от уровня вакансии и ответов кандидата.\n"
            "Задавай вопросы, чтобы оценить все важные для вакансии навыки. \n"
            "Обрати внимание на уровень вакансии и задавай соответствующие ему вопросы.\n"
            "Задавай вопросы по очереди, после ответа кандидата на предыдущий вопрос задай следующий.\n"
            "Вопросы должны быть короткие и легкие для понимания.\n"
            "После вопросов спроси, есть ли вопросы у кандидата, и ответь на них, строго в рамках вакансии.\n"
            "Если кандидат явно не подходит или диалог логически завершен, используй функцию end_dialog."
        )

        if self.vacancy:
            return f"{base_prompt}\n\nВот вакансия:\n{self.vacancy}"
        else:
            return base_prompt

    def _define_functions(self) -> List[Dict]:
        """Определение функций доступных модели"""
        return [
            {
                "name": "end_dialog",
                "description": "Завершает диалог с кандидатом. Используется когда все вопросы заданы и дан ответ на все вопросы кандидата, кандидат не подходит или диалог логически завершен.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Причина завершения диалога"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Краткое резюме диалога"
                        }
                    },
                    "required": ["reason", "summary"]
                }
            }
        ]

    def _initialize_dialog(self):
        """Инициализация диалога с системным промптом"""
        self.messages = [
            Messages(role=MessagesRole.SYSTEM, content=self.system_prompt)
        ]
        self.dialog_active = True
        self.dialog_history = []

    def _save_dialog_to_file(self) -> str:
        """Сохранение диалога в файл. Возвращает путь к файлу."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dialog_history_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Вакансия: {self.vacancy}\n\n")
            f.write("История диалога по ролям кандидат и AI HR:\n\n")

            for role, message in self.dialog_history:
                if role == "AI HR":
                    f.write(f"AI HR: {message}\n")
                elif role == "Кандидат":
                    f.write(f"Кандидат: {message}\n")
                else:
                    f.write(f"{role}: {message}\n")

        logger.info(f"Диалог сохранен в файл: {filename}")
        return filename

    def end_dialog(self, reason: str, summary: str) -> str:
        """
        Завершение диалога - функция вызываемая моделью

        Args:
            reason: Причина завершения диалога
            summary: Краткое резюме диалога

        Returns:
            Подтверждение завершения диалога
        """
        self.dialog_active = False
        result = f"Диалог завершен. Причина: {reason}. Резюме: {summary}"
        self.dialog_history.append(("AI HR", result))
        logger.info(f"Ассистент завершил диалог: {result}")

        self._save_dialog_to_file()
        return result

    def _process_function_call(self, function_name: str, arguments: Dict) -> Any:
        """
        Обработка вызова функции моделью
        """
        if function_name == "end_dialog":
            return self.end_dialog(
                reason=arguments.get("reason", "Диалог завершен"),
                summary=arguments.get("summary", "Резюме не предоставлено")
            )
        else:
            return f"Функция {function_name} не найдена"

    def send_message(self, user_input: str) -> str:
        """
        Отправка сообщения и получение ответа от модели

        Args:
            user_input: Ввод пользователя

        Returns:
            Ответ модели GigaChat или результат вызова функции
        """
        if not self.dialog_active:
            return "Диалог уже завершен. Начните новый диалог."

        self.dialog_history.append(("Кандидат", user_input))
        self.messages.append(Messages(role=MessagesRole.USER, content=user_input))

        try:
            chat_request = Chat(
                messages=self.messages,
                functions=self.functions,
                function_call="auto"
            )

            response = self.giga.chat(chat_request)
            message = response.choices[0].message

            # Обработка вызова функции моделью
            if hasattr(message, 'function_call') and message.function_call:
                function_call = message.function_call
                function_name = function_call.name

                # Парсинг аргументов
                if hasattr(function_call, 'arguments'):
                    if isinstance(function_call.arguments, str):
                        try:
                            arguments = json.loads(function_call.arguments)
                        except json.JSONDecodeError:
                            arguments = {"reason": "Неверный формат аргументов", "summary": "Ошибка парсинга аргументов"}
                    elif isinstance(function_call.arguments, dict):
                        arguments = function_call.arguments
                    else:
                        arguments = {"reason": "Неизвестный формат аргументов", "summary": "Ошибка обработки аргументов"}
                else:
                    arguments = {"reason": "Аргументы не предоставлены", "summary": "Отсутствуют аргументы функции"}

                function_result = self._process_function_call(function_name, arguments)

                self.messages.append(Messages(
                    role=MessagesRole.ASSISTANT,
                    content="",
                    function_call=function_call
                ))

                self.messages.append(Messages(
                    role=MessagesRole.FUNCTION,
                    content=function_result,
                    name=function_name
                ))

                return function_result
            else:
                assistant_response = message.content
                self.dialog_history.append(("AI HR", assistant_response))
                self.messages.append(Messages(
                    role=MessagesRole.ASSISTANT,
                    content=assistant_response
                ))
                return assistant_response

        except Exception as e:
            error_msg = f"Произошла ошибка при отправке сообщения в GigaChat: {str(e)}"
            logger.exception(error_msg)
            self.dialog_history.append(("AI HR", error_msg))
            return error_msg

    def is_dialog_active(self) -> bool:
        return self.dialog_active

    def get_dialog_history(self) -> List[Dict]:
        return self.messages

    def set_vacancy(self, vacancy: str):
        self.vacancy = vacancy
        self.system_prompt = self._create_system_prompt()
        self._initialize_dialog()
