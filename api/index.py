import os
import sys

# Add project root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure VERCEL environment flag is set
os.environ["VERCEL"] = "1"

from src.app import app

__all__ = ["app"]
