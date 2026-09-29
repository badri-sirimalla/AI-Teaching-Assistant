"""Shared Flask extension instances, kept separate from app.py to avoid
circular imports between app.py, models.py, and the route blueprints."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
