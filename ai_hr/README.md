## ML
This service provides the conference pipeline and analytics for interviews. It accepts connections via WebSocket and starts a live interview based on vacancy requirements and candidate's resume.
## API-key
To use this service you need to set API_KEY (GigaChat API KEY), API_KEY_SALUTE and USER_ID (Client ID in Studio) via Sber Studio. 

[Get SaluteSpeech API Key & Client-Id](https://developers.sber.ru/docs/ru/salutespeech/api/authentication)

[Get GigaChat API key](https://developers.sber.ru/docs/ru/gigachat/individuals-quickstart)

## Build
To build the service use ```docker compose up -d```, note that installing dependencies may take a sufficient amount of time (required disk space ~8 Gb)