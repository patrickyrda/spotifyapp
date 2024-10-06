from flask import Flask
from app.routes.routes import routes
from app.config import Config  # Import your config class

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load the configuration

    # Register your blueprint
    app.register_blueprint(routes)

    return app
