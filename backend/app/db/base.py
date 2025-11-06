"""
SQLAlchemy database base configuration.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create base class for all models
Base = declarative_base()

# Note: Do NOT import models here to avoid circular imports
# Models will be imported in alembic/env.py for migrations
