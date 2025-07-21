import requests
import datetime
import os
from dotenv import load_dotenv


load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LLM_API_KEY = os.environ['LLM_API_KEY']
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_last_commits(owner, repo):
    since = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=24)).isoformat() + "Z"
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"since": since, "per_page": 100}
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

def summarize_with_llm(commits):
    prompt = f"""You are a helpful assistant that summarizes GitHub commit diffs.

    Here are the commits:
    {commits}

    Please write a concise summary of the changes made in these commits.
    """

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "input": prompt,
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()
    return result["output"][0]["content"][0]["text"]

def main():
    commits = get_last_commits(REPO_OWNER, REPO_NAME)

    stringOfCommits = ""
    for commit in commits:
        sha = commit["sha"]
        message = commit["commit"]["message"]
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"]

        try:
            diff = get_commit_diff(REPO_OWNER, REPO_NAME, sha)
            stringOfCommits = stringOfCommits + f"Commit {sha[:7]} by {author} on {date}:\n{diff[:12000]}\n\n"
        except Exception as e:
            print(f"⚠️ Failed to process commit {sha[:7]}: {e}")

    summary = summarize_with_llm(stringOfCommits)
    print(summary)

if __name__ == "__main__":
    main()