# Imagen base con Python 3.10 (versión slim para que sea ligera)
FROM python:3.10-slim

# Evita archivos .pyc y hace que los logs salgan en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crea un usuario no-root por seguridad
RUN useradd -m appuser

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema (útil si pandas/numpy necesitan compilación)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo tu código al contenedor
COPY . .

# Cloud Run inyecta el puerto en la variable $PORT (por defecto 8080)
ENV PORT=8080
EXPOSE 8080

# Cambia a usuario seguro
USER appuser

# Arranca Streamlit usando tu archivo dashboard.py
CMD ["sh", "-c", "streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0"]
