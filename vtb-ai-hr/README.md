# Backend
## Build
Run ```docker compose up -d``` to run the service and it's requirements. We use ```PostgreSQL``` and ```Minio``` for storing photos, resumes and vacancies.
### Populate database
If you want to run backend with mock data you can set ```POPULATE_DATABASE=true``` in .env file. See examples of entity creation in ```populate.py```.
## API & Docs
You can access Swagger UI by [link](localhost:9200/docs). It can help you test how the backend features work. 