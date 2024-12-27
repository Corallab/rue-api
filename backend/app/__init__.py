from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Update CORS configuration to allow frontend access
    CORS(
        app,
        resources={r"/*": {"origins": ["http://192.168.0.3:3001", "http://localhost:3001"]}},
        supports_credentials=True
    )

    Config.validate()

    # Import and register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
