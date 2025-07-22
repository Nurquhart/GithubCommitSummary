/* These should most likely be moved to credentials service */
%let LLM_API_KEY = %sysget(LLM_API_KEY);
%let GITHUB_TOKEN = %sysget(GITHUB_TOKEN);
%let GRANT_TYPE = %sysget(GRANT_TYPE);

/* Python script to fetch commit diffs and summarize them with OpenAI */
proc python;
submit;

import requests
import datetime
import os

GITHUB_TOKEN = SAS.symget("GITHUB_TOKEN")
LLM_API_KEY = SAS.symget("LLM_API_KEY")
REPO_OWNER = "Nurquhart"
REPO_NAME = "GithubCommitSummary"

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Computes the time 24 hours ago, and grabs all the commits since then
def get_last_commits(owner, repo):
    since = (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat() + "Z"
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"since": since, "per_page": 100}
    response = requests.get(url, headers=GITHUB_HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# Gets a diff for a given commit
def get_commit_diff(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    headers = GITHUB_HEADERS.copy()
    headers["Accept"] = "application/vnd.github.v3.diff"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

# sends a string of commit info to OpenAI for a summary of what changed
# inside of the respository
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

#
# Fetch the commits
# Fetch diffs for each commit
# Summarize them with OpenAI and create a txt file with the response
#
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
        print(f"Failed to process commit {sha[:7]}: {e}")

summary = summarize_with_llm(stringOfCommits)
print(summary)

# Add microsoft api or Studio midtier to send email instead of create file
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H%M")
with open(f"/dmtesting/naurqu/summarize-commits/commit_summary{timestamp}.txt", "w", encoding="utf-8") as f:
    f.write(summary)

# set a global variable with the summary to be used below
SAS.submit(f'%let summary_from_python = {summary};')
endsubmit;
quit;

/* 
Now send an email with the summary results
*/

filename tokrep temp;

proc http
    url="https://daily.pgc.unx.sas.com/SASLogon/oauth/token"
    method="POST"
    in="&GRANT_TYPE"
    out=tokrep;
    headers
        "Authorization"="Basic c2FzLmVjOg==" 
        "Content-Type"="application/x-www-form-urlencoded";
run;

libname tokenlib json fileref=tokrep;

/* Extract the token into a macro variable */
data _null_;
    set tokenlib.alldata;
    if upcase(scan(p1, -1, '.')) = "ACCESS_TOKEN" then
        call symputx('access_token', value, 'G');
run;

%put &=access_token;



filename emres temp;
filename emreq temp;

/* Write the JSON payload to a file */
data _null_;
    file emreq;
    put '{';
    put '  "to": [';
    put '    { "address": "Nurquhart014@gmail.com" }';
    put '  ],';
    put '  "from": { "address": "Nathan.Urquhart@sas.com" },';
    put '  "subject": "Repository Highlights",';
    put "  ""textMessage"": ""&summary_from_python""";
    put '}';
run;

proc http
    url= "https://daily.pgc.unx.sas.com/mail/messages" /* Replace with real endpoint */
    method="POST"
    in=emreq
    out=emres;
    headers
        "Authorization"="Bearer &access_token"
        "Content-Type"="application/json";
run;