from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import requests
import os
from dotenv import load_dotenv
import subprocess

# Describe the model we are using
model = OllamaLLM(model="llama3.2")

# Create a chain to summarize each commit individually
template = """
Here is a git commit that was recently merged into my GitHub repository: \nCommit message:\n{message}\n\nDiff:\n{diff}

Can you briefly summarize the changes made in this commit?
Please provide a concise summary that captures the essence of the changes, including any significant additions, deletions, or modifications to the codebase.
Focus on the overall impact of the commit rather than specific line-by-line changes.
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

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

def summarize_individually_with_ollama(message, diff):
    result = chain.invoke({"message": message, "diff": diff})
    return result

def main():
    commits = get_last_commits(REPO_OWNER, REPO_NAME)

    arrOfSummaries = []
    for commit in commits:
        sha = commit["sha"]
        message = commit["commit"]["message"]
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"]

        try:
            diff = get_commit_diff(REPO_OWNER, REPO_NAME, sha)
            summary = summarize_individually_with_ollama(message, diff[:12000])
            labeledSummary = f"Commit {sha[:7]} by {author} on {date}:\n{summary}"
            arrOfSummaries.append(labeledSummary)
        except Exception as e:
            print(f"⚠️ Failed to process commit {sha[:7]}: {e}")
    print("Summary of the last 10 commits:")
    print("\n")
    for summary in arrOfSummaries:
        print(summary)
        print("\n\n")

if __name__ == "__main__":
    main()