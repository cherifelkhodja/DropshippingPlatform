"""SQLAlchemy Declarative Base.

Provides the base class for all ORM models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All ORM models should inherit from this class.
    """

    pass
