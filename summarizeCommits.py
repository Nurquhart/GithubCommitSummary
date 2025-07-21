from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import requests
import datetime
import os
from dotenv import load_dotenv
import subprocess

# Describe the model we are using
model = OllamaLLM(model="llama3.2")

# Create a chain to summarize each commit individually
template = """
Here is a list of commits that were recently merged into my GitHub repository: \n{commits}

Can you briefly summarize the changes made in all of these commits?
Please provide a concise summary that captures the essence of the changes, including any significant additions, deletions, or modifications to the codebase.
Focus on the overall impact of the commit rather than specific line-by-line changes.
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

OLLAMA_MODEL = "llama3"  # or mistral, phi3, etc.

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

def summarize_with_ollama(commits):
    result = chain.invoke({"commits": commits})
    return result

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

    summary = summarize_with_ollama(stringOfCommits)
    print(summary)

if __name__ == "__main__":
    main()