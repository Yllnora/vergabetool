# Basis-Image: aktuelles Python
FROM python:3.12

# Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere requirements & installiere
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Projektcode
COPY . .

# Starte den Django-Server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
