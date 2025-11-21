from github import Github
import os
import base64

def get_repo():
    """Lazy initialization of GitHub client"""
    g = Github(os.getenv("GITHUB_TOKEN"))
    return g.get_repo(os.getenv("GITHUB_REPO"))

def create_pr(title: str, body: str, branch: str, files: dict):
    """Create a pull request with file changes"""
    try:
        repo = get_repo()
        # files = {"path/to/file.py": "new content"}
        base = repo.get_branch("master")
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=base.commit.sha)

        for path, content in files.items():
            try:
                f = repo.get_contents(path, ref="master")
                repo.update_file(path, f"Patch {path}", content, f.sha, branch=branch)
            except:
                repo.create_file(path, f"Add {path}", content, branch=branch)

        pr = repo.create_pull(title=title, body=body, head=branch, base="master")
        return pr.html_url
    except Exception as e:
        print(f"GitHub PR creation failed: {e}")
        return f"https://github.com/{os.getenv('GITHUB_REPO')}/pulls"