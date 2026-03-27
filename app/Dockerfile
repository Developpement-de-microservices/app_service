FROM python:3.11-slim

LABEL maintainer="Florent L. <59474408+flo-lec@users.noreply.github.com>"
LABEL description="Microservice for the management of apps and their versions."
LABEL service="app_service"

WORKDIR /app
COPY app/requirements.txt .
COPY app/app.py .

RUN pip install -r requirements.txt

EXPOSE 5001
CMD ["python", "app.py"]