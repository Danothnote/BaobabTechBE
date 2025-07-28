FROM tiangolo/uvicorn-gunicorn-fastapi:latest

WORKDIR /app

RUN pip freeze > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
