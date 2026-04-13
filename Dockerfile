# Usa una versione leggera di Python
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file di dipendenze
COPY requirements.txt .

# Installa i pacchetti richiesti
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutti i file del progetto
COPY . .

# Espone la porta 5000 per Flask
EXPOSE 8000

# Comando di avvio
CMD ["python", "app.py"]
