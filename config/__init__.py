"""Config package bridge for Daphne.

This package exists so imports like "config.asgi:application"
work. See config/asgi.py for the export.
"""

__all__ = ["asgi"]
