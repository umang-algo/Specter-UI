import os
import sys
from github import Github
from dotenv import load_dotenv

def main():
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not found in .env")
        sys.exit(1)

    print("🔑 Authenticating with GitHub...")
    g = Github(token)
    user = g.get_user()
    
    repo_name = "DevAgent-Swarm"
    print(f"📦 Creating repository {repo_name} for user {user.login}...")
    
    try:
        repo = user.create_repo(
            name=repo_name,
            description="Autonomous, omniscient coding swarm. Clones repos, drives native Claude Code CLI, features SSE web dashboard and PR automation.",
            private=False,
            has_issues=True,
            has_projects=False,
            has_wiki=False
        )
        print(f"✅ Successfully created repository: {repo.html_url}")
        print(f"ssh_url: {repo.ssh_url}")
        print(f"clone_url: {repo.clone_url}")
    except Exception as e:
        print(f"⚠️ Failed to create repository (maybe it already exists?): {e}")

if __name__ == "__main__":
    main()
