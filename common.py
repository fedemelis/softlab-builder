from main import *

def is_valid_github_username(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    return response.status_code == 200


# testing the GitHub token
def is_valid_github_token(token, repository_name):
    try:
        g = Github(token)
        repo = g.get_user().get_repo(repository_name)

        # it tries to create a test file
        try:
            repo.create_file("test.txt", "Creating test file", "test content")
        except GithubException as e:
            if e.status == 422 and "sha" in str(e):
                # ignore the error "Invalid request. \"sha\" wasn't supplied."
                pass
            else:
                raise

        # it tries to remove the test file
        try:
            file = repo.get_contents("test.txt")
            repo.delete_file(file.path, "Removing test file", file.sha)
        except GithubException as e:
            if e.status == 404:
                pass
            else:
                raise

        return True
    except Exception as e:
        print(e)
        return False


def build_dir_hierarchy():
    if not os.path.exists(os.path.join("data")):
        os.mkdir(os.path.join("data"))
    if not os.path.exists(os.path.join("data", "heading")):
        os.mkdir(os.path.join("data", "heading"))
    if not os.path.exists(os.path.join("data", "images")):
        os.mkdir(os.path.join("data", "images"))
