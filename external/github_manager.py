# Enhanced GitHub Manager for InsightFactory
import os
import sys
from git import Repo
import time
from datetime import datetime

class GitHubManager:
    def __init__(self, repo_path, github_token=None):
        self.repo_path = repo_path
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.repo = self._init_repo()
        
    def _init_repo(self):
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            repo = Repo.init(self.repo_path)
            # Configure git credentials if token is provided
            if self.github_token:
                with open(os.path.join(self.repo_path, '.git', 'config'), 'a') as f:
                    f.write('\n[credential]\n\thelper = store\n')
        else:
            repo = Repo(self.repo_path)
        return repo
    
    def add_and_commit(self, message=None):
        if not message:
            message = f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add all changes
        self.repo.git.add(all=True)
        
        # Only commit if there are changes
        if self.repo.is_dirty() or len(self.repo.untracked_files) > 0:
            self.repo.index.commit(message)
            return True
        return False
    
    def push_to_remote(self, remote_name='origin', branch='main'):
        try:
            if remote_name not in [remote.name for remote in self.repo.remotes]:
                print(f"Remote {remote_name} not found. Please set up remote first.")
                return False
            
            if self.github_token:
                # Use token in the URL for authentication
                remote_url = self.repo.remotes[remote_name].url
                if not remote_url.startswith('https://'):
                    print("Remote URL must use HTTPS for token authentication")
                    return False
                auth_url = f"https://{self.github_token}@{remote_url[8:]}"
                self.repo.git.push(f"https://{self.github_token}@github.com/Jedward23/InsightFactory.git", branch)
            else:
                self.repo.git.push(remote_name, branch)
            return True
        except Exception as e:
            print(f"Error pushing to remote: {str(e)}")
            return False
            
    def setup_remote(self, url, remote_name='origin'):
        try:
            if remote_name not in [remote.name for remote in self.repo.remotes]:
                self.repo.create_remote(remote_name, url)
            return True
        except Exception as e:
            print(f"Error setting up remote: {str(e)}")
            return False
            
    def auto_sync(self, interval=1800):  # 30 minutes default
        while True:
            if self.add_and_commit():
                self.push_to_remote()
            time.sleep(interval)
