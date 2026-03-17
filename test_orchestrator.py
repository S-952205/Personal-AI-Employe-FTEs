"""Test orchestrator with single email"""
from scripts.orchestrator import Orchestrator
from pathlib import Path

vault_path = Path('personal-ai-employee').absolute()
print(f"Vault path: {vault_path}")

orchestrator = Orchestrator(vault_path, check_interval=30)
print("Running single cycle...")
orchestrator.run_once()
print("\n=== Cycle Complete ===")
print("Check folders:")
print("  - Pending_Approval: For approval requests")
print("  - Done: For completed items")
