"""
NEXUS-NER | pytest configuration
Adds the AI root directory to sys.path so all modules can be imported.
"""
import sys
from pathlib import Path

# Make sure all modules are importable from tests/
AI_ROOT = Path(__file__).resolve().parent
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))
