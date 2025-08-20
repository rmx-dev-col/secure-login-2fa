import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta  # Importa timedelta aquí

# Cargar las variables del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # 🔑 Claves de seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SECRET_KEY_RESET = os.environ.get("SECRET_KEY_RESET", "dev-reset-secret-change-me")
    FERNET_KEY = os.environ.get("FERNET_KEY", "default-fernet-key")

    # 📦 Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance/app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ⚙️ Debug solo en desarrollo
    DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1")

    # 📧 Configuración de correo
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # Configuración de sesión
    SESSION_COOKIE_NAME = "your_session_cookie"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Duración de la sesión
