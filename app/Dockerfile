FROM python:3.11-slim

LABEL maintainer="Florent L. <59474408+flo-lec@users.noreply.github.com>"
LABEL description="Microservice for the management of apps and their versions."
LABEL service="app_service"

WORKDIR /app
COPY app/requirements.txt .
COPY app/app.py .

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:5001/apps/health || exit 1

EXPOSE 5001
CMD ["python", "app.py"]