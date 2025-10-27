# On prend Python 3.11
FROM python:3.11-slim

# Dossier de travail
WORKDIR /app

# On copie tout le projet
COPY . .

# On installe les dépendances
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# On lance le bot
CMD ["python", "main.py"]
