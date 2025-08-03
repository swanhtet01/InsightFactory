import os
from pathlib import Path
import threading
from external.github_manager import GitHubManager

def start_github_sync():
    repo_path = str(Path(__file__).resolve().parent.parent)
    github_manager = GitHubManager(repo_path)
    
    # Set up remote if needed
    github_manager.setup_remote("https://github.com/Jedward23/InsightFactory.git")
    
    # Start auto-sync in a background thread (30 minute intervals)
    sync_thread = threading.Thread(target=github_manager.auto_sync, daemon=True)
    sync_thread.start()
    return github_manager

def upload_report_to_github(report_path, commit_message, repo_path=None):
    repo_path = repo_path or str(Path(__file__).resolve().parent.parent)
    manager = GitHubManager(repo_path)
    manager.add_and_commit(commit_message)
    manager.push_to_remote()
