from flask import current_app
from flask_login import UserMixin
from app import db, bcrypt
from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import URLSafeTimedSerializer
import os
import secrets
import json
from typing import Optional
from datetime import datetime
import pytz  # Para manejar las zonas horarias

# Configuración de clave de cifrado
FERNET_KEY = os.environ.get("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY no configurada. Exporta FERNET_KEY en variables de entorno.")
fernet = Fernet(FERNET_KEY)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret_encrypted = db.Column(db.LargeBinary, nullable=True)

    recovery_codes_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Métodos de contraseña
    def set_password(self, password: str) -> None:
        """Encripta y establece la contraseña del usuario."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña es válida."""
        return bcrypt.check_password_hash(self.password_hash, password)

    # Métodos de 2FA
    def set_2fa_secret(self, secret: Optional[str]) -> None:
        """Cifra y guarda el secreto 2FA."""
        if secret is None:
            self.two_factor_secret_encrypted = None
        else:
            self.two_factor_secret_encrypted = fernet.encrypt(secret.encode())

    def get_2fa_secret(self) -> Optional[str]:
        """Descifra y devuelve el secreto 2FA."""
        if not self.two_factor_secret_encrypted:
            return None
        try:
            return fernet.decrypt(self.two_factor_secret_encrypted).decode()
        except InvalidToken:
            return None

    def disable_2fa(self) -> None:
        """Desactiva 2FA y borra el secreto."""
        self.two_factor_enabled = False
        self.two_factor_secret_encrypted = None
        self.recovery_codes_json = None

    # Métodos de códigos de recuperación
    def generate_recovery_codes(self, count: int = 5) -> list[str]:
        """Genera múltiples códigos de recuperación y los guarda hashed."""
        codes = []
        hashed_codes = []

        for _ in range(count):
            raw_code = secrets.token_hex(8)
            codes.append(raw_code)
            hashed_codes.append(
                bcrypt.generate_password_hash(raw_code).decode("utf-8")
            )

        self.recovery_codes_json = json.dumps(hashed_codes)
        return codes

    def verify_recovery_code(self, code: str) -> bool:
        """Verifica si un código de recuperación es válido y lo invalida tras usarlo."""
        if not self.recovery_codes_json:
            return False

        hashed_codes = json.loads(self.recovery_codes_json)

        for stored_hash in hashed_codes:
            if bcrypt.check_password_hash(stored_hash, code):
                hashed_codes.remove(stored_hash)
                self.recovery_codes_json = json.dumps(hashed_codes)
                return True

        return False

    # Métodos de restablecimiento de contraseña
    def get_reset_token(self, expires_sec: int = 1800) -> str:
        """Genera un token de reseteo válido (30 min por defecto)."""
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token: str, max_age: int = 1800) -> Optional["User"]:
        """Verifica un token de reseteo. Retorna el usuario o None."""
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token, max_age=max_age)
            user_id = data["user_id"]
        except Exception:
            return None
        return User.query.get(user_id)

    # Actualización de último login (Ajustado para zona horaria de Colombia)
    def update_last_login(self) -> None:
        """Actualiza la fecha/hora del último inicio de sesión en hora local (Colombia)."""
        colombia_tz = pytz.timezone('America/Bogota')  # Zona horaria de Colombia
        self.last_login = datetime.now(colombia_tz)  # Usamos la hora local de Colombia
        db.session.commit()

