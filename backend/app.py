"""
Flask app entry point. Run with:  python app.py
(from inside the backend/ directory, with the virtualenv active)
"""
from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db

from routes.upload import upload_bp
from routes.videos import videos_bp
from routes.chat import chat_bp
from routes.health import health_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=[Config.FRONTEND_ORIGIN])

    db.init_app(app)

    app.register_blueprint(upload_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)

    with app.app_context():
        Config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
