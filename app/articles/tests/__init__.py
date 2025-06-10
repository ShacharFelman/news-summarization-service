"""
Articles app test utilities.

This module exposes common test utilities to be used across all test modules.
It provides factory functions and URL helpers to avoid code duplication.
"""
import logging

# Suppress expected warning logs from request handling
logging.getLogger('django.request').setLevel(logging.ERROR)

from .utils import (
    create_article,
    list_url,
    detail_url,
)

__all__ = [
    'create_article',
    'list_url',
    'detail_url',
]