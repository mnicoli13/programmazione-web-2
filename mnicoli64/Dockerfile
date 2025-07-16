# 1. Base image: Python ufficiale, slim per risparmiare spazio
FROM python:3.11-slim

# 2. Imposto la working directory nel container
WORKDIR /app

# 3. Copio solo requirements.txt e installo le dipendenze
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 4. Copio tutto il codice del progetto
COPY . .

# 5. Espongo la porta sulla quale Django gira di default
EXPOSE 8000

# 6. Comando di default per avviare il container
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
