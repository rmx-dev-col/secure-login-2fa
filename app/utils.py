import pyotp
import qrcode
from . import mail  # Importa la instancia de mail desde __init__.py
import io
import base64
from cryptography.fernet import Fernet
from qrcode.image.pil import PilImage  # Necesita Pillow
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app, url_for, render_template
from flask_mail import Message
from .models import db, User  # Asegúrate de importar el modelo User y db

# -----------------------------
# Clave de cifrado
# -----------------------------
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise ValueError(
        "La clave FERNET_KEY no está configurada en las variables de entorno. "
        "Agrega FERNET_KEY en tu archivo .env"
    )
fernet = Fernet(FERNET_KEY)

# -----------------------------
# Funciones para cifrar/descifrar
# -----------------------------
def encrypt_secret(secret: str) -> str:
    """Cifra una clave secreta con Fernet."""
    return fernet.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret: str) -> str:
    """Descifra una clave secreta con Fernet."""
    return fernet.decrypt(encrypted_secret.encode()).decode()

# -----------------------------
# Funciones para 2FA
# -----------------------------
def generate_2fa_secret(encrypt: bool = True) -> str:
    secret = pyotp.random_base32()
    if encrypt:
        return encrypt_secret(secret)
    return secret

def get_qr_data_uri(username: str, encrypted_secret: str, issuer="RMX CYBERTECH") -> str:
    secret = decrypt_secret(encrypted_secret)
    uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        image_factory=PilImage
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buff = io.BytesIO()
    img.save(buff, format="PNG")
    b64 = base64.b64encode(buff.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

def verify_totp(encrypted_secret: str, token: str, valid_window: int = 1) -> bool:
    secret = decrypt_secret(encrypted_secret)
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=valid_window)

def generate_recovery_code(user_id: int) -> str:
    return pyotp.random_base32()

def regenerate_2fa_secret(user_id: int) -> str:
    new_secret = generate_2fa_secret()
    user = User.query.get(user_id)
    if user:
        user.set_2fa_secret(new_secret)
        db.session.commit()
    return new_secret

# -----------------------------
# Funciones para reset password
# -----------------------------
def get_serializer():
    """Genera el serializador para tokens seguros."""
    secret_key = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key)

def generate_reset_token(user: User, expires_sec: int = 1800) -> str:
    """
    Genera un token para resetear contraseña.
    :param user: Usuario
    :param expires_sec: Tiempo de validez en segundos (default 30 min)
    """
    s = get_serializer()
    return s.dumps({"user_id": user.id})

def verify_reset_token(token: str, max_age: int = 1800):
    """
    Verifica y devuelve el usuario asociado a un token de reset.
    :param token: El token recibido en el email.
    :param max_age: Tiempo máximo de validez en segundos.
    :return: Instancia de User o None
    """
    s = get_serializer()
    try:
        data = s.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(data["user_id"])

def send_reset_email(user: User):
    """
    Envía un email al usuario con el link de recuperación de contraseña.
    Incluye tanto texto plano como HTML (template).
    """
    token = generate_reset_token(user)
    reset_url = url_for("auth.reset_password", token=token, _external=True)  # Corregido

    msg = Message(
        "Recupera tu contraseña",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email]
    )

    # Texto plano (fallback por si no soporta HTML)
    msg.body = f"""
    Hola {user.username},

    Para restablecer tu contraseña, haz clic en el siguiente enlace:
    {reset_url}

    Si no solicitaste este cambio, ignora este correo.
    """

    # HTML con template
    msg.html = render_template("email/reset_password.html", user=user, reset_url=reset_url)

    from . import mail  # importamos mail ya inicializado en __init__.py
    mail.send(msg)
