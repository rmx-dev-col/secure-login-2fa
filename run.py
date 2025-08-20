from app import create_app

app = create_app()

if __name__ == "__main__":
    # Corre la app en todas las interfaces y puerto 5000 con debug activo
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
