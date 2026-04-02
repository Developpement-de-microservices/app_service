# Utilisation d'une base Alpine ultra-légère (~5Mo l'OS seul)
FROM python:3.14-alpine3.23

LABEL maintainer="Florent L. <59474408+flo-lec@users.noreply.github.com>"
LABEL description="Microservice for the management of apps and their versions."
LABEL service="app_service"

WORKDIR /app

RUN apk add --no-cache curl

COPY app/requirements.txt .
COPY app/app.py .

RUN pip install --no-cache-dir -r requirements.txt

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5001/apps/health || exit 1

EXPOSE 5001
CMD ["python", "app.py"]