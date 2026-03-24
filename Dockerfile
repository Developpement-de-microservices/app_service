FROM python:3.11-slim
WORKDIR /app_service
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]