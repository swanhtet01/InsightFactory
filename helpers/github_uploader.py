import os
from pathlib import Path
import threading
from external.github_manager import GitHubManager

def start_github_sync():
    repo_path = str(Path(__file__).resolve().parent.parent)
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("⚠️ No GITHUB_TOKEN found in environment. GitHub sync will be disabled.")
        return None
    
    github_manager = GitHubManager(repo_path, token)
    
    try:
        # Set up remote if needed (use token in URL)
        remote_url = f"https://{token}@github.com/swanhtet01/InsightFactory.git"
        github_manager.setup_remote(remote_url)
        
        # Start auto-sync in a background thread (30 minute intervals)
        sync_thread = threading.Thread(target=github_manager.auto_sync, daemon=True)
        sync_thread.start()
        print("✅ GitHub sync enabled and running in background")
        return github_manager
    except Exception as e:
        print(f"⚠️ Failed to start GitHub sync: {e}")
        return None

def upload_report_to_github(report_path, commit_message, repo_path=None):
    repo_path = repo_path or str(Path(__file__).resolve().parent.parent)
    manager = GitHubManager(repo_path)
    manager.add_and_commit(commit_message)
    manager.push_to_remote()
