"""
Root-level pytest configuration.

Ensures the project root is in sys.path so backend module can be imported.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
