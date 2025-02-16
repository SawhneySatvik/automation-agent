

import os, re, subprocess
import datetime, git
from fastapi import HTTPException


def clone_and_commit(filename, targetfile):
    print(f"Cloning repository... {filename}, {targetfile}")
    if not filename or not targetfile:
        raise HTTPException(status_code=400, detail="Invalid input parameters: .git file and target file are required.")
    REPO_URL = filename
    LOCAL_PATH = f"./data/{get_repo_name(REPO_URL)}"
    COMMIT_MESSAGE = "Updated example.txt"
    FILENAME = "example.txt"
    NEW_CONTENT = "This is a new change!\n" + str(datetime.datetime.now())

    curr_dir = os.getcwd()
    try:
        # Clone the repository if not already cloned
        if not os.path.exists(LOCAL_PATH):
            repo = git.Repo.clone_from(REPO_URL, LOCAL_PATH)
        else:
            repo = git.Repo(LOCAL_PATH)
            repo.remotes.origin.pull()  # Pull latest changes

        # Ensure the working directory is clean
        repo.git.checkout('main')  # Switch to main branch (change if needed)

        # Ensure the file exists before writing
        file_path = os.path.join(LOCAL_PATH, FILENAME)

        # Create or overwrite the file
        with open(file_path, "w") as f:
            f.write(NEW_CONTENT)

        # Change to the cloned repository directory
        os.chdir(LOCAL_PATH)
        # Verify the current working directory
        print("Current Directory:", os.getcwd())

        # Stage and commit the changes
        #repo.index.add([file_path])
        repo.git.add(A=True)
        repo.index.commit(COMMIT_MESSAGE)

        # Push changes (ensure authentication)
        origin = repo.remotes.origin
        origin.push()

        print("Changes committed and pushed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        raise e
    finally:
        os.chdir(curr_dir)  # Change back to original directory

def get_repo_name(repo_url):
    match = re.search(r"([^/]+)\.git$", repo_url)
    return match.group(1) if match else None
