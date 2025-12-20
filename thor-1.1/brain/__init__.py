"""
Brain package exposing connectors and shared paths.
"""
from pathlib import Path

DATA_DIR = Path(__file__).parent

from .connector import BrainConnector  # noqa: F401

