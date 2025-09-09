import os
from dotenv import load_dotenv
import requests
from pydub import AudioSegment
from io import BytesIO
import json
import subprocess
from pydub.utils import which


class SberSpeechAPI:
    def __init__(self, api_key_salute, user_id):
        self.api_key_salute = api_key_salute
        self.user_id = user_id

    def _get_token(self):
        """Получение нового токена"""
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        payload = {'scope': 'SALUTE_SPEECH_PERS'}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.user_id,
            'Authorization': f'Basic {self.api_key_salute}'
        }

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            verify=False
        )
        response.raise_for_status()

        return response.json()['access_token']

    def tts(self, text):
        """Преобразование текста в речь с возвратом WebM в виде байтов"""
        access_token = self._get_token()

        url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
        headers = {
            'Content-Type': 'application/text',
            'Accept': 'audio/webm',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(
            url,
            headers=headers,
            data=text.encode('utf-8'),
            verify=False
        )
        response.raise_for_status()

        return response.content

    def asr(self, webm_data):
        """Распознавание речи из WebM данных, возвращает строку"""
        access_token = self._get_token()

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        ffmpeg_command = [
            ffmpeg_path,
            '-i', 'pipe:0',
            '-acodec', 'libopus',
            '-ac', '1',
            '-ar', '16000',
            '-f', 'ogg',
            'pipe:1'
        ]

        try:
            process = subprocess.Popen(
                ffmpeg_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            opus_data, stderr = process.communicate(input=webm_data)

            if process.returncode != 0:
                print(f"Ошибка ffmpeg: {stderr.decode()}")
                return ""

        except Exception as e:
            print(f"Ошибка при конвертации аудио: {e}")
            return ""

        url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
        headers = {
            'Content-Type': 'audio/ogg;codecs=opus',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=opus_data,
                verify=False
            )
            response.raise_for_status()

            result = response.json()
            if isinstance(result, dict) and 'result' in result:
                return result['result']
            elif isinstance(result, list) and len(result) > 0:
                return str(result[0])
            else:
                return str(result)

        except requests.exceptions.HTTPError as e:
            print(f"Ошибка при распознавании речи: {e}")
            print(f"Статус код: {e.response.status_code}")
            return ""
        except Exception as e:
            print(f"Ошибка при распознавании речи: {e}")
            return ""


load_dotenv()


if __name__ == "__main__":
    # from API_KEY import api_key_salute, user_id
    api_key_salute = os.getenv("API_KEY_SALUTE")
    user_id = os.getenv("USER_ID")

    sber_speech = SberSpeechAPI(api_key_salute, user_id)

    # Синтез речи
    webm_data = sber_speech.tts("Привет мир! Это тест синтеза речи.")

    # Сохранение в файл
    with open("output.webm", "wb") as f:
        f.write(webm_data)
    print("Аудио сохранено в output.webm")

    # Распознавание речи
    text = sber_speech.asr(webm_data)
    print(f"Распознанный текст: {text}")
