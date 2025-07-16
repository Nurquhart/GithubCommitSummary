import requests
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

OLLAMA_MODEL = "llama3"  # or mistral, phi3, etc.

REPO_OWNER = "Nurquhart"
REPO_NAME = "GithubCommitSummary"

def get_last_commits(owner, repo, count=10):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": count}
    response = requests.get(url, headers=GITHUB_HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_commit_diff(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    headers = GITHUB_HEADERS.copy()
    headers["Accept"] = "application/vnd.github.v3.diff"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def summarize_with_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.stdout.decode()

def main():
    commits = get_last_commits(REPO_OWNER, REPO_NAME)

    for commit in commits:
        sha = commit["sha"]
        message = commit["commit"]["message"]
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"]
        print(f"\n\n\n")
        print(f"\n🔍 Commit {sha[:7]} by {author} on {date}")
        print(f"\n\n")
        print(f"{message}")

        # try:
        #     diff = get_commit_diff(REPO_OWNER, REPO_NAME, sha)
        #     full_prompt = f"Summarize the following Git commit.\n\nCommit message:\n{message}\n\nDiff:\n{diff[:12000]}"
        #     summary = summarize_with_ollama(full_prompt)
        #     print(f"📝 Summary:\n{summary.strip()}")
        # except Exception as e:
        #     print(f"⚠️ Failed to process commit {sha[:7]}: {e}")

if __name__ == "__main__":
    main()