"""Test audit logger directly"""
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent
sys.path.insert(0, str(scripts_path))

from audit_logger import AuditLogger

print("Creating audit logger...")
audit = AuditLogger(Path('personal-ai-employee'))
print(f"✓ Audit logger created: {audit}")

print("\nLogging test email...")
audit.log_email_send(
    to='test@example.com',
    subject='Test from test_audit.py',
    result='success',
    approval_status='approved',
    approved_by='test_script'
)
print("✓ Log call completed!")

print("\nCheck the log file now!")
