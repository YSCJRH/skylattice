"""Hosted web control-plane helpers."""

from .config import WebConnectorConfig
from .connector import SkylatticeWebConnector

__all__ = ["SkylatticeWebConnector", "WebConnectorConfig"]
