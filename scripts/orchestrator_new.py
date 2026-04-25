"""
Orchestrator for AI Employee - Silver Tier

Enhanced orchestrator with HITL (Human-in-the-Loop) workflow,
multi-watcher support, and MCP server integration.

Uses Kilo Code for AI reasoning and processing.
"""

import subprocess
import logging
import time
import json
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

# Fix UnicodeEncodeError for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import audit logger for Gold Tier compliance
sys.path.insert(0, str(Path(__file__).parent))
from audit_logger import get_audit_logger, AuditLogger
from ralph_wiggum import RalphWiggumLoop
from cross_domain_integration import DomainClassifier, ApprovalThresholdManager

# â”€â”€â”€ LOGGING SETUP â”€â”€â”€
file_handler = logging.FileHandler('logs/orchestrator.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
console_handler.setLevel(logging.INFO)

