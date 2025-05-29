def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ... suas configurações, blueprints, etc.

    return app  # ✅ ESSA LINHA É OBRIGATÓRIA
