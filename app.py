from auditoria_app import create_app

app = create_app()
print("SECRET_KEY:", app.config.get("SECRET_KEY"))

if __name__ == '__main__':
    app.run(debug=True)
