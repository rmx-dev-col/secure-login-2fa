# 🔐 Secure Login 2FA

Aplicación web en Flask con autenticación segura de usuarios:  
✅ Registro/Login  
✅ Recuperación de contraseñas vía email  
✅ Códigos de recuperación  
✅ 2FA con QR y tokens TOTP  
✅ Dashboard protegido  


## 🚀 Requisitos

- Python 3.8+
- Virtualenv (opcional pero recomendado)
- SQLite (incluido en Python)



## ⚙️ Instalación

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/rmx-dev-col/secure-login-2fa.git
   cd secure-login-2fa
Crear y activar entorno virtual

bash
Copiar
Editar
python3 -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
Instalar dependencias

bash
Copiar
Editar
pip install -r requirements.txt
Crear archivo .env (basado en .env.example)

bash
Copiar
Editar
cp .env.example .env
Aquí configuras tus claves secretas, base de datos, etc.

Generar la base de datos

bash
Copiar
Editar
flask db upgrade
Esto creará instance/app.db vacío con las tablas necesarias.
⚠️ Nota: No incluimos una base real en el repo por seguridad.
Cada desarrollador debe generar la suya localmente con este comando.

▶️ Ejecución
bash
Copiar
Editar
flask run
Abrir en: http://localhost:5000

👨‍💻 Notas de desarrollo
El archivo .env y app.db NO deben subirse al repo.

Puedes regenerar la base en cualquier momento con:

bash
Copiar
Editar
rm instance/app.db
flask db upgrade
📂 Estructura del proyecto
csharp
Copiar
Editar
secure-login-2fa/
│── app/              # Código principal (modelos, rutas, forms, utils)
│── migrations/       # Migraciones de Alembic
│── static/           # Archivos estáticos (css, js, imágenes)
│── templates/        # Plantillas HTML (Jinja2)
│── instance/         # Contendrá app.db (no se sube al repo)
│── .env.example      # Ejemplo de configuración
│── requirements.txt  # Dependencias
│── run.py            # Punto de entrada
✨ Features por implementar
Roles de usuario (admin, user)

Logs de actividad

Integración con correo real (SMTP)

Test unitarios con Pytest

📜 Licencia
MIT License - libre para usar y modificar.
