from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo

# Expresión regular para contraseña segura
password_regex = (
    r'^(?=.*[a-z])'         # Minúscula
    r'(?=.*[A-Z])'          # Mayúscula
    r'(?=.*\d)'             # Número
    r'(?=.*[!@#$%^&*()_\-+=\[{\]};:\'",<.>/?\\|`~])'  # Símbolo
    r'.{8,}$'               # Longitud mínima 8
)

class ForgotPasswordForm(FlaskForm):
    """Formulario para solicitar un enlace de recuperación de contraseña."""
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Ingrese un email válido.")
        ]
    )
    submit = SubmitField("Enviar enlace de recuperación")


class RegisterForm(FlaskForm):
    """Formulario de Registro para nuevos usuarios."""
    username = StringField(
        "Usuario",
        validators=[
            DataRequired(),
            Length(min=3, max=64, message="El usuario debe tener entre 3 y 64 caracteres.")
        ]
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Ingrese un email válido.")
        ]
    )
    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(),
            Regexp(
                password_regex,
                message="Debe tener mínimo 8 caracteres, incluyendo mayúsculas, minúsculas, números y símbolos."
            )
        ]
    )
    submit = SubmitField("Registrarse")


class LoginForm(FlaskForm):
    """Formulario de Login para usuarios existentes."""
    username = StringField("Usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember = BooleanField("Recordarme")
    submit = SubmitField("Entrar")


class ResetPasswordForm(FlaskForm):
    """Formulario para restablecer la contraseña (nueva password)."""
    password = PasswordField(
        "Nueva contraseña",
        validators=[
            DataRequired(),
            Regexp(
                password_regex,
                message="Debe tener mínimo 8 caracteres, incluyendo mayúsculas, minúsculas, números y símbolos."
            )
        ]
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="Las contraseñas deben coincidir.")
        ]
    )
    submit = SubmitField("Restablecer contraseña")


class TwoFactorForm(FlaskForm):
    """Formulario para configurar el 2FA (código de la app de autenticación)."""
    token = StringField(
        "Código 2FA",
        validators=[DataRequired()],
        render_kw={"placeholder": "Introduce el código de la app"}
    )
    submit = SubmitField("Activar 2FA")
