
import asyncio
import json
import time
from typing import Optional
from dialog_voice import SberSpeechAPI
from dialog_giigachat import HRAssistant, GigaChatModel
from analyzer import LLMAnalyzer
import os
from io import StringIO
from pydub import AudioSegment
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import logging
import argparse
import sys

import time

import asyncio
from fastapi import FastAPI, WebSocket
from typing import Optional
import os
from io import StringIO, BytesIO
import wave
import struct
from dotenv import load_dotenv

load_dotenv()

# Парсим аргументы командной строки для получения vacancy


def parse_args():
    parser = argparse.ArgumentParser(description='Conference Pipeline')
    parser.add_argument('--vacancy', type=str, required=True,
                        help='Vacancy description')
    return parser.parse_args()


app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем параметры из переменных среды
api_key = os.getenv('API_KEY')
api_key_salute = os.getenv('API_KEY_SALUTE')
user_id = os.getenv('USER_ID')

# Проверяем, что все необходимые переменные окружения установлены
if not api_key or not api_key_salute or not user_id:
    raise ValueError(
        "Необходимо установить переменные окружения: API_KEY, API_KEY_SALUTE, USER_ID")

# Получаем vacancy из аргументов командной строки


class ConferencePipeline:
    def __init__(self, vacancy_text: str | None = None):
        # Инициализация модулей
        self.dialog_voice = SberSpeechAPI(
            api_key_salute,
            user_id
        )

        self.dialog = HRAssistant(
            api_key,
            model=GigaChatModel.LITE,
            vacancy=vacancy_text  # текст вакансии из CLI
        )

        # Передаем текст вакансии, а не путь к файлу
        self.review = LLMAnalyzer(
            api_key,
            db_api_url=os.getenv("REVIEW_DB_URL")
        )

        self.is_processing = False
        self.audio_buffer = StringIO()
        self.empty_count = 0

    def raw_audio_to_webm(self, raw_audio_data: bytes) -> bytes:
        """Конвертация сырых аудиоданных в WebM формат"""
        wav_buffer = BytesIO()
        sample_rate = 44100
        channels = 1
        sample_width = 2

        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(raw_audio_data)
        wav_buffer.seek(0)
        wav_data = wav_buffer.read()
        return wav_data

    async def process_websocket(self, websocket: WebSocket):
        """Обработка WebSocket соединения"""
        await websocket.accept()

        # 0. Воспроизведение приветственного сообщения
        welcome_text = "Здравствуйте, я ассистент ВТБ. Давайте начнем собеседование."
        welcome_audio = self.dialog_voice.tts(welcome_text)
        await websocket.send_bytes(welcome_audio)

        while True:
            try:
                # 1. Получение сырых аудиоданных от конференции
                raw_audio_data = await websocket.receive_bytes()

                # Конвертация в WebM
                webm_data = self.raw_audio_to_webm(raw_audio_data)

                if not self.is_processing:
                    # 2. Распознавание речи
                    asr_result = self.dialog_voice.asr(webm_data)
                    print(
                        f"Тип asr_result: {type(asr_result)}, Значение: '{asr_result}'")

                    asr_text = ""
                    if isinstance(asr_result, list) and len(asr_result) > 0:
                        asr_text = str(
                            asr_result[0]) if asr_result[0] is not None else ""
                    elif isinstance(asr_result, dict):
                        asr_text = str(asr_result.get('result', ''))
                    elif asr_result is not None:
                        asr_text = str(asr_result)

                    print(
                        f"Извлеченный asr_text: Тип {type(asr_text)}, Значение: '{asr_text}'")

                    if not asr_text or not isinstance(asr_text, str) or not asr_text.strip():
                        self.empty_count += 1
                        print(
                            f"Пустой текст, увеличиваем empty_count: {self.empty_count}")
                    else:
                        self.empty_count = 0
                        self.audio_buffer.write(asr_text + " ")
                        print(
                            f"Добавлен текст в буфер: '{asr_text}', buffer_size: {self.audio_buffer.tell()}")

                    print(
                        f"empty_count: {self.empty_count}, buffer_size: {self.audio_buffer.tell()}")

                    # 3. Запуск генерации после 3 пустых ответов
                    if self.empty_count >= 3 and self.audio_buffer.tell() > 0:
                        self.is_processing = True
                        user_text = self.audio_buffer.getvalue().strip()
                        self.audio_buffer = StringIO()
                        print(f"Отправляем в Dialog: '{user_text}'")

                        # 4. Генерация ответа
                        response = self.dialog.send_message(user_text)
                        print(f"Получен ответ от Dialog: '{response}'")

                        if not self.dialog.is_dialog_active():
                            # 5. Завершение конференции
                            await websocket.send_json({"action": "end_conference"})
                            await websocket.close()
                            break

                        # 6. Преобразование текста в речь
                        response_audio = self.dialog_voice.tts(response)
                        await websocket.send_bytes(response_audio)

                        with open("output.webm", "wb") as f:
                            f.write(response_audio)

                        # Сбрасываем счетчики после отправки ответа
                        self.is_processing = False
                        self.empty_count = 0
                        print(
                            f"Сбросили счетчики: empty_count={self.empty_count}, is_processing={self.is_processing}")

            except WebSocketDisconnect:
                logger.info("WebSocket отключен клиентом")
                break
            except Exception as e:
                logger.error(f"Ошибка в процессе WebSocket: {e}")
                break

        # 6. Отправка истории в review (анализатор)
        history_text = self._format_dialog_history()
        print(f"История диалога: {history_text}")

        if history_text.strip():
            try:
                review_result = self.review.analyze_text(self.vacancy_text, history_text)
                print(f"Результат анализа: {review_result}")
                # 7. Сохранение в БД (заглушка)
                self._save_to_db(review_result)
            except Exception as e:
                logger.error(f"Ошибка при анализе: {e}")
                self._save_to_db(json.dumps(
                    {"error": str(e)}, ensure_ascii=False))
        else:
            print("История диалога пуста — анализ не выполняется.")

    def _format_dialog_history(self) -> str:
        """Форматирование истории диалога: только ответы кандидата (клиента)"""
        user_messages = [
            message for role, message in self.dialog.dialog_history
            if role == "client" and isinstance(message, str) and message.strip()
        ]

        # Оставляем только непустые строки
        cleaned_messages = [msg.strip()
                            for msg in user_messages if msg.strip()]

        return json.dumps(cleaned_messages, ensure_ascii=False)

    def _save_to_db(self, result: str):
        """Заглушка для сохранения в БД"""
        print(f"Результат для сохранения в БД: {result}")
        # Здесь можно добавить POST-запрос к REVIEW_DB_URL, если нужно
