FROM python:3.9

WORKDIR /app

COPY app/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["python", "-m", "uvicorn", "app.transport.rest:app", "--host", "0.0.0.0", "--port", "8000"]