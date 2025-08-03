import os
import sys
from external.github_manager import GitHubManager

def setup_github_sync():
    # Get the GitHub token from environment or prompt user
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        github_token = input("Please enter your GitHub token: ").strip()
        os.environ['GITHUB_TOKEN'] = github_token
    
    # Initialize GitHub manager with the repo path
    repo_path = os.path.dirname(os.path.abspath(__file__))
    manager = GitHubManager(repo_path, github_token)
    
    # Set up the remote repository
    remote_url = "https://github.com/Jedward23/InsightFactory.git"
    manager.setup_remote(remote_url)
    
    # Do initial commit if needed
    manager.add_and_commit("Initial commit")
    
    # Start auto-sync in background
    try:
        manager.auto_sync()
    except KeyboardInterrupt:
        print("\nGitHub sync stopped.")

if __name__ == "__main__":
    setup_github_sync()
