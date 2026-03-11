#!/usr/bin/env python3
"""Test script to run the server"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the server
from app.api.simple_server import run_server

if __name__ == "__main__":
    run_server()