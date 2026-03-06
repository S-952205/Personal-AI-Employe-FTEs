"""
File System Watcher for AI Employee - Bronze Tier

Monitors the /Inbox folder for new files and creates action files in /Needs_Action.
This is the simplest watcher implementation for the Bronze tier.
"""

import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/filesystem_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FileSystemWatcher')


class InboxFileHandler(FileSystemEventHandler):
    """Handles file creation events in the Inbox folder."""
    
    def __init__(self, vault_path: Path):
        super().__init__()
        self.vault_path = vault_path
        self.needs_action = vault_path / 'Needs_Action'
        self.processed_files = set()
        
        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_id(self, filepath: Path) -> str:
        """Generate a unique ID for a file based on its name and modification time."""
        content = f"{filepath.name}{filepath.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _create_metadata_file(self, source: Path, action_file: Path) -> Path:
        """Create a metadata markdown file in Needs_Action."""
        file_id = self._generate_file_id(source)
        metadata_path = self.needs_action / f'FILE_{file_id}.md'
        
        # Get file size in human-readable format
        size_bytes = source.stat().st_size
        size_kb = size_bytes / 1024
        size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
        
        content = f"""---
type: file_drop
original_name: {source.name}
original_path: {source.absolute()}
size: {size_str}
received: {datetime.now().isoformat()}
priority: normal
status: pending
file_id: {file_id}
---

# File Dropped for Processing

**Original File:** `{source.name}`

**Location:** `{action_file.name}`

**Size:** {size_str}

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Suggested Actions

- [ ] Review file content
- [ ] Process or categorize
- [ ] Move to appropriate folder
- [ ] Archive when complete

---

## Processing Notes

_Add your notes here_

"""
        metadata_path.write_text(content, encoding='utf-8')
        logger.info(f"Created action file: {metadata_path.name}")
        return metadata_path
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        source_path = Path(event.src_path)
        
        # Skip hidden files and temporary files
        if source_path.name.startswith('.') or source_path.suffix in ['.tmp', '.swp']:
            return
        
        # Skip if already processed
        file_id = self._generate_file_id(source_path)
        if file_id in self.processed_files:
            return
        
        logger.info(f"New file detected: {source_path.name}")
        
        try:
            # Copy file to Inbox (if not already there)
            inbox_path = self.vault_path / 'Inbox' / source_path.name
            if source_path != inbox_path:
                import shutil
                shutil.copy2(source_path, inbox_path)
                logger.info(f"Copied to Inbox: {inbox_path.name}")
            
            # Create action file in Needs_Action
            self._create_metadata_file(source_path, inbox_path)
            self.processed_files.add(file_id)
            
        except Exception as e:
            logger.error(f"Error processing file {source_path.name}: {e}")


class FileSystemWatcher:
    """Main watcher class that monitors the Inbox folder."""
    
    def __init__(self, vault_path: str, check_interval: int = 5):
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        
        # Ensure Inbox directory exists
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        
        self.event_handler = InboxFileHandler(self.vault_path)
        self.observer = None
    
    def start(self):
        """Start the file system watcher."""
        logger.info(f"Starting FileSystemWatcher for: {self.inbox_path}")
        
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.inbox_path),
            recursive=False
        )
        self.observer.start()
        logger.info("FileSystemWatcher started successfully")
    
    def run(self):
        """Run the watcher in a blocking loop."""
        self.start()
        
        try:
            while True:
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def stop(self):
        """Stop the file system watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("FileSystemWatcher stopped")


def main():
    """Main entry point for the file system watcher."""
    # Get the vault path (personal-ai-employee folder)
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'
    
    logger.info(f"Vault path: {vault_path}")
    logger.info(f"Inbox path: {vault_path / 'Inbox'}")
    logger.info("Press Ctrl+C to stop the watcher")
    
    watcher = FileSystemWatcher(str(vault_path))
    watcher.run()


if __name__ == '__main__':
    main()
