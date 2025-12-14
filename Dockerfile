# Base image sifatida Python rasmiy kichik hajmli versiyasidan foydalanish
FROM python:3.11-slim

# Ishchi katalogini belgilash
WORKDIR /app

# Requirements faylini nusxalash va kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Boshqa barcha fayllarni (main.py) nusxalash
COPY . .

# Botni ishga tushirish komandasi
CMD ["python", "main.py"]

