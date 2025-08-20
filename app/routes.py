from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_mail import Message
from flask_login import login_user, logout_user, current_user
from .models import User
from . import db, mail
from .forms import ForgotPasswordForm, ResetPasswordForm, LoginForm, RegisterForm, TwoFactorForm
import pyotp
import qrcode

bp = Blueprint("auth", __name__)

# Ruta principal que redirige a login
@bp.route("/", methods=["GET"])
def home():
    return redirect(url_for('auth.login'))  # Redirige al login

# Ruta para mostrar la página de login
@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()  # Crea una instancia del formulario

    if request.method == "POST" and form.validate_on_submit():
        # Lógica de validación de login
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):  # Asegúrate de que check_password esté bien implementado en User
            flash("¡Bienvenido de nuevo!", "success")
            login_user(user)  # Asegúrate de que esta línea esté presente para autenticar al usuario
            user.update_last_login()  # Actualiza el último login
            return redirect(url_for('auth.dashboard'))  # Redirige al dashboard
        else:
            flash("Credenciales incorrectas. Inténtalo de nuevo.", "error")

    return render_template("login.html", form=form)

# Ruta para mostrar la página de recuperación de contraseña
@bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            msg = Message(
                'Recuperación de contraseña',
                sender='no-reply@tu-dominio.com',
                recipients=[form.email.data]
            )
            msg.body = f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}"

            try:
                mail.send(msg)
                flash("Un enlace de recuperación ha sido enviado a tu correo.", "info")
                return redirect(url_for('auth.login'))
            except Exception as e:
                flash(f"Ocurrió un error al enviar el correo: {e}", "error")
        else:
            flash("No se encontró un usuario con ese correo electrónico.", "error")

    return render_template("forgot_password.html", form=form)

# Ruta para mostrar la página de registro
@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()  # Crea una instancia del formulario de registro

    if request.method == "POST" and form.validate_on_submit():
        # Lógica de validación del registro
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash("El nombre de usuario ya está en uso. Por favor, elige otro.", "error")
        else:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data  # La contraseña se encripta automáticamente en el setter
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Cuenta creada con éxito. Puedes iniciar sesión ahora.", "success")
            return redirect(url_for('auth.login'))

    return render_template("register.html", form=form)

# Ruta para la página de restablecimiento de contraseña
@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        user = User.verify_reset_token(token)
        if user:
            user.set_password(form.password.data)  # Encripta la nueva contraseña
            db.session.commit()
            flash("Tu contraseña ha sido actualizada.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("El enlace de recuperación es inválido o ha caducado.", "error")

    return render_template("reset_password.html", form=form)

# Ruta para el Dashboard
@bp.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        flash("Debes iniciar sesión primero.", "error")
        return redirect(url_for('auth.login'))  # Redirige si no está autenticado
    
    return render_template("dashboard.html")

# Ruta para el logout
@bp.route("/logout")
def logout():
    logout_user()  # Elimina la sesión del usuario
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('auth.login'))  # Redirige al login

# Ruta para la configuración de 2FA
@bp.route("/setup_2fa", methods=["GET", "POST"])
def setup_2fa():
    if not current_user.is_authenticated:
        flash("Debes iniciar sesión primero.", "error")
        return redirect(url_for('auth.login'))

    form = TwoFactorForm()  # Crea una instancia del formulario de 2FA

    if form.validate_on_submit():
        # Lógica para verificar y activar el 2FA
        token = form.token.data  # Obtiene el código ingresado por el usuario

        # Aquí debería validarse el token con la librería pyotp
        user = User.query.filter_by(id=current_user.id).first()  # Obtén al usuario actual
        totp = pyotp.TOTP(user.get_2fa_secret())  # Usamos el secreto del usuario para verificar el token

        if totp.verify(token):
            flash("2FA activado correctamente.", "success")
            return redirect(url_for('auth.dashboard'))  # Redirige al dashboard
        else:
            flash("El código de 2FA es incorrecto. Inténtalo de nuevo.", "error")

    # Lógica para generar el QR del 2FA
    user = User.query.filter_by(id=current_user.id).first()  # Obtén al usuario actual
    totp = pyotp.TOTP(user.get_2fa_secret())  # Usa el secreto del usuario
    uri = totp.provisioning_uri(current_user.username, issuer_name="TuAplicación")

    # Generar el código QR
    img = qrcode.make(uri)
    img_path = f"static/img/2fa_qr_{current_user.id}.png"
    img.save(img_path)

    return render_template("setup_2fa.html", form=form, qr=img_path)
