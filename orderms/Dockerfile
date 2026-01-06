FROM python:3.11-slim

WORKDIR /app

# Gerekli paketleri kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port aç
EXPOSE 8082

# Uygulamayı başlat
CMD ["python", "app.py"]