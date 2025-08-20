from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from datetime import datetime

from .forms import (
    RegisterForm, LoginForm, TwoFactorForm, RecoveryForm,
    RequestResetForm, ResetPasswordForm
)
from .models import User
from . import db, mail
from .utils import generate_2fa_secret, get_qr_data_uri, verify_totp

auth_bp = Blueprint("auth", __name__)

# --- Serializer para tokens de reset ---
def get_serializer():
    # Usamos SECRET_KEY por compatibilidad
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


# --- Index ---
@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


# --- Registro ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash("Usuario o email ya registrado.", "danger")
            return render_template("register.html", form=form)

        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


# --- Login ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash("Usuario o contraseña incorrecta.", "danger")
            return render_template("login.html", form=form)

        # Verificación 2FA
        if user.two_factor_enabled:
            session["pre_2fa_user_id"] = user.id
            return redirect(url_for("auth.twofactor"))

        # Login normal sin 2FA
        login_user(user, remember=form.remember.data)
        user.update_last_login()  # ⬅️ Actualizar último login
        flash("Bienvenido, has iniciado sesión.", "success")
        return redirect(url_for("auth.dashboard"))

    return render_template("login.html", form=form)


# --- Verificación 2FA ---
@auth_bp.route("/twofactor", methods=["GET", "POST"])
def twofactor():
    form = TwoFactorForm()
    uid = session.get("pre_2fa_user_id")
    if not uid:
        return redirect(url_for("auth.login"))

    user = User.query.get(uid)
    if not user:
        session.pop("pre_2fa_user_id", None)
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        secret = user.get_2fa_secret()
        if secret and verify_totp(secret, form.token.data.strip(), valid_window=1):
            login_user(user)
            user.update_last_login()  # ⬅️ Actualizar último login
            session.pop("pre_2fa_user_id", None)
            flash("Inicio de sesión con 2FA correcto.", "success")
            return redirect(url_for("auth.dashboard"))
        flash("Código 2FA incorrecto.", "danger")

    return render_template("twofactor.html", form=form)


# --- Activar 2FA ---
@auth_bp.route("/setup-2fa", methods=["GET", "POST"])
@login_required
def setup_2fa():
    if current_user.two_factor_enabled:
        flash("2FA ya está activado.", "info")
        return redirect(url_for("auth.dashboard"))

    secret = session.get("tmp_2fa_secret") or generate_2fa_secret()
    session["tmp_2fa_secret"] = secret

    current_user.set_2fa_secret(secret)
    db.session.commit()

    qr = get_qr_data_uri(current_user.username, secret)
    form = TwoFactorForm()

    if form.validate_on_submit():
        if verify_totp(secret, form.token.data.strip(), valid_window=1):
            current_user.two_factor_enabled = True
            recovery_codes = current_user.generate_recovery_codes()
            db.session.commit()
            session.pop("tmp_2fa_secret", None)
            flash("2FA activado correctamente. Guarda tus códigos de recuperación en un lugar seguro.", "success")
            return render_template("recovery_codes.html", codes=recovery_codes)
        flash("Código inválido. Intenta de nuevo.", "danger")

    return render_template("twofactor.html", form=form, qr=qr, setup=True)


# --- Recuperación con códigos ---
@auth_bp.route("/recovery", methods=["GET", "POST"])
def recovery():
    form = RecoveryForm()
    if form.validate_on_submit():
        recovery_code = form.recovery_code.data.strip()
        users = User.query.filter(User.recovery_codes_json.isnot(None)).all()
        for u in users:
            if u.verify_recovery_code(recovery_code):
                login_user(u)
                u.update_last_login()  # ⬅️ Actualizar último login
                db.session.commit()
                flash("Recuperación exitosa. Has iniciado sesión.", "success")
                return redirect(url_for("auth.dashboard"))

        flash("Código de recuperación incorrecto.", "danger")
        return render_template("recovery.html", form=form)

    return render_template("recovery.html", form=form)


# --- Reset Password Request ---
@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            s = get_serializer()
            token = s.dumps(user.email, salt="reset-password")
            link = url_for("auth.reset_password", token=token, _external=True)

            # --- Enviar email con nueva plantilla ---
            msg = Message("Recupera tu contraseña", recipients=[user.email])
            msg.html = render_template(
                "email/email_reset.html",
                user=user,
                link=link,
                current_year=datetime.utcnow().year
            )
            mail.send(msg)

        flash("Si el correo existe, recibirás un enlace para resetear la contraseña.", "info")
        return redirect(url_for("auth.login"))

    return render_template("reset_password_request.html", form=form)


# --- Reset Password con token ---
@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt="reset-password", max_age=600)  # 10 minutos
    except (SignatureExpired, BadSignature):
        flash("El enlace no es válido o ha expirado.", "danger")
        return redirect(url_for("auth.reset_password_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Usuario no encontrado.", "danger")
            return redirect(url_for("auth.reset_password_request"))

        user.set_password(form.password.data)
        db.session.commit()
        flash("Tu contraseña fue actualizada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)


# --- Dashboard ---
@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# --- Logout ---
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cierre de sesión correcto.", "info")
    return redirect(url_for("auth.login"))
