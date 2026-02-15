"""Expose the project's ASGI application as `config.asgi:application`.
"""
from ecommerce_project.asgi import application

__all__ = ["application"]
