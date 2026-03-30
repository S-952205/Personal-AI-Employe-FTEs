"""
Audit Logger for AI Employee - Gold Tier Compliance

Stores audit logs in /Vault/Logs/YYYY-MM-DD.json format as required by hackathon blueprint.
Retains logs for minimum 90 days.

Hackathon Requirement (Section 6.3):
  "Store logs in /Vault/Logs/YYYY-MM-DD.json and retain for a minimum 90 days."

Usage:
    from audit_logger import AuditLogger
    
    audit = AuditLogger(vault_path)
    audit.log(
        action_type="email_send",
        actor="orchestrator",
        target="client@example.com",
        parameters={"subject": "Invoice #123"},
        approval_status="approved",
        approved_by="human",
        result="success"
    )
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AuditLogger:
    """
    Audit logger that stores actions in JSON format in the vault.
    Compliant with hackathon requirement Section 6.3.
    """
    
    def __init__(self, vault_path: Path, retention_days: int = 90):
        self.vault_path = vault_path
        self.logs_folder = vault_path / 'Logs'
        self.retention_days = retention_days
        
        # Ensure logs folder exists
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Today's log file
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.logs_folder / f'{self.today}.json'
        
        # Setup standard logging as backup
        self._setup_backup_logging()
    
    def _setup_backup_logging(self):
        """Setup traditional logging as backup."""
        backup_log = self.logs_folder / 'audit_backup.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(backup_log, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.backup_logger = logging.getLogger('AuditLogger')
    
    def log(self, 
            action_type: str,
            actor: str,
            target: str,
            result: str,
            parameters: Optional[Dict[str, Any]] = None,
            approval_status: Optional[str] = None,
            approved_by: Optional[str] = None,
            source_item: Optional[str] = None,
            message_id: Optional[str] = None,
            error: Optional[str] = None):
        """
        Log an action to the daily JSON audit log.
        
        Args:
            action_type: Type of action (email_send, archive, approval_create, etc.)
            actor: Who performed the action (orchestrator, gmail_watcher, etc.)
            target: Target of the action (email address, file path, etc.)
            result: Outcome (success, failure, skipped, etc.)
            parameters: Additional parameters (subject, content, etc.)
            approval_status: pending, approved, rejected (if applicable)
            approved_by: human, auto, system (if applicable)
            source_item: Original file/item that triggered this action
            message_id: Gmail message ID or other external reference
            error: Error message if result is failure
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "result": result,
        }
        
        # Add optional fields if provided
        if parameters:
            entry["parameters"] = parameters
        if approval_status:
            entry["approval_status"] = approval_status
        if approved_by:
            entry["approved_by"] = approved_by
        if source_item:
            entry["source_item"] = source_item
        if message_id:
            entry["message_id"] = message_id
        if error:
            entry["error"] = error
        
        # Append to daily log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            self.backup_logger.info(f"Audit log entry: {action_type} → {result}")
            
        except Exception as e:
            self.backup_logger.error(f"Failed to write audit log: {e}")
    
    def log_email_send(self, to: str, subject: str, result: str, 
                       message_id: Optional[str] = None,
                       error: Optional[str] = None,
                       approval_status: str = "approved",
                       approved_by: str = "human",
                       source_item: Optional[str] = None):
        """Convenience method for logging email sends."""
        self.log(
            action_type="email_send",
            actor="orchestrator",
            target=to,
            result=result,
            parameters={"subject": subject},
            message_id=message_id,
            error=error,
            approval_status=approval_status,
            approved_by=approved_by,
            source_item=source_item
        )
    
    def log_email_archive(self, email_file: str, reason: str, actor: str = "email_processor"):
        """Convenience method for logging email archives."""
        self.log(
            action_type="email_archive",
            actor=actor,
            target=email_file,
            result="success",
            parameters={"reason": reason},
            approval_status="auto_approved",
            approved_by="system"
        )
    
    def log_approval_create(self, approval_file: str, action_type: str,
                           source_item: str, actor: str = "orchestrator"):
        """Convenience method for logging approval creation."""
        self.log(
            action_type="approval_create",
            actor=actor,
            target=approval_file,
            result="success",
            parameters={"approval_action": action_type},
            approval_status="pending",
            approved_by=None,
            source_item=source_item
        )
    
    def log_approval_action(self, approval_file: str, action: str,
                           actor: str = "human"):
        """Convenience method for logging approval actions (approve/reject)."""
        self.log(
            action_type=f"approval_{action}",  # approve or reject
            actor=actor,
            target=approval_file,
            result="success",
            approval_status=action,
            approved_by=actor
        )
    
    def log_watcher_detection(self, watcher: str, item_type: str,
                             item_id: str, count: int = 1):
        """Convenience method for logging watcher detections."""
        self.log(
            action_type="watcher_detection",
            actor=watcher,
            target=item_id,
            result="success",
            parameters={"item_type": item_type, "count": count}
        )
    
    def log_error(self, error_type: str, actor: str, target: str,
                 error_message: str, source_item: Optional[str] = None):
        """Convenience method for logging errors."""
        self.log(
            action_type=f"error_{error_type}",
            actor=actor,
            target=target,
            result="failure",
            error=error_message,
            source_item=source_item
        )
    
    def cleanup_old_logs(self) -> int:
        """
        Remove/archive logs older than retention_days.
        Returns number of files cleaned up.
        """
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        cleaned = 0
        
        for log_file in self.logs_folder.glob('*.json'):
            try:
                # Parse date from filename (YYYY-MM-DD.json)
                file_date = datetime.strptime(log_file.stem, '%Y-%m-%d')
                
                if file_date < cutoff:
                    # Archive old log (compress and move)
                    archive_folder = self.logs_folder / 'archive'
                    archive_folder.mkdir(parents=True, exist_ok=True)
                    
                    archive_name = f"{log_file.stem}_archived.json"
                    archive_path = archive_folder / archive_name
                    
                    log_file.rename(archive_path)
                    cleaned += 1
                    
                    self.backup_logger.info(f"Archived old log: {log_file.name}")
                    
            except Exception as e:
                self.backup_logger.error(f"Error cleaning up log {log_file.name}: {e}")
        
        return cleaned
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for a given day.
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Dictionary with counts by action type and result
        """
        if date is None:
            date = self.today
        
        log_file = self.logs_folder / f'{date}.json'
        
        if not log_file.exists():
            return {"error": f"No log file for {date}"}
        
        summary = {
            "date": date,
            "total_actions": 0,
            "by_action_type": {},
            "by_result": {},
            "by_actor": {},
            "emails_sent": 0,
            "emails_archived": 0,
            "approvals_created": 0,
            "approvals_approved": 0,
            "approvals_rejected": 0,
            "errors": 0
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    summary["total_actions"] += 1
                    
                    # Count by action type
                    action_type = entry.get("action_type", "unknown")
                    summary["by_action_type"][action_type] = summary["by_action_type"].get(action_type, 0) + 1
                    
                    # Count by result
                    result = entry.get("result", "unknown")
                    summary["by_result"][result] = summary["by_result"].get(result, 0) + 1
                    
                    # Count by actor
                    actor = entry.get("actor", "unknown")
                    summary["by_actor"][actor] = summary["by_actor"].get(actor, 0) + 1
                    
                    # Specific counts
                    if action_type == "email_send":
                        summary["emails_sent"] += 1
                    elif action_type == "email_archive":
                        summary["emails_archived"] += 1
                    elif action_type == "approval_create":
                        summary["approvals_created"] += 1
                    elif action_type == "approval_approve":
                        summary["approvals_approved"] += 1
                    elif action_type == "approval_reject":
                        summary["approvals_rejected"] += 1
                    elif action_type.startswith("error_"):
                        summary["errors"] += 1
                        
        except Exception as e:
            self.backup_logger.error(f"Error reading log file: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """
        Generate a markdown report for a given day.
        Can be saved to vault for Obsidian viewing.
        """
        summary = self.get_daily_summary(date)
        
        if "error" in summary and len(summary) == 1:
            return f"# Audit Report - {date}\n\nNo data available.\n"
        
        report = f"""# Audit Report - {summary['date']}

## Summary

| Metric | Count |
|--------|-------|
| Total Actions | {summary['total_actions']} |
| Emails Sent | {summary['emails_sent']} |
| Emails Archived | {summary['emails_archived']} |
| Approvals Created | {summary['approvals_created']} |
| Approvals Approved | {summary['approvals_approved']} |
| Approvals Rejected | {summary['approvals_rejected']} |
| Errors | {summary['errors']} |

## By Action Type

| Action Type | Count |
|-------------|-------|
"""
        
        for action_type, count in sorted(summary['by_action_type'].items()):
            report += f"| {action_type} | {count} |\n"
        
        report += f"""
## By Result

| Result | Count |
|--------|-------|
"""
        
        for result, count in sorted(summary['by_result'].items()):
            report += f"| {result} | {count} |\n"
        
        report += f"""
## By Actor

| Actor | Count |
|-------|-------|
"""
        
        for actor, count in sorted(summary['by_actor'].items()):
            report += f"| {actor} | {count} |\n"
        
        report += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(vault_path: Optional[Path] = None) -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    
    if _audit_logger is None:
        if vault_path is None:
            raise ValueError("vault_path required for first call to get_audit_logger()")
        _audit_logger = AuditLogger(vault_path)
    
    return _audit_logger


def log_audit(**kwargs):
    """Convenience function to log an audit entry."""
    logger = get_audit_logger()
    logger.log(**kwargs)
