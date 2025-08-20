from flask import Flask
from flask_migrate import MigrateCommand
from flask_script import Manager
from app import create_app, db

app = create_app()
manager = Manager(app)

# Agrega el comando de migración
from flask_migrate import Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    manager.run()
