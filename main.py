import base64
import json
import os
import re
import string
import threading
import time
from datetime import datetime
from tokenize import String

import requests as requests
from github import GithubException, Github
from openai import OpenAI


def user_input_thread():
    global should_exit
    user_input = input("Type \"yes\" to stop: ")
    if user_input == "si" or user_input == "Si" or user_input == "SI" or user_input == "yes" or user_input == "Yes" or \
            user_input == "YES":
        should_exit = True
        print("Quitting...")


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


def retrieve_repo(source, personal_key):
    url = f"https://api.github.com/users/{source}/repos"
    headers = {"Authorization": f"Bearer {personal_key}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        public_repos = [repo["name"] for repo in response.json()]
        return public_repos
    else:
        print(f"Error {response.status_code}: Cannot retrieve a list of public repos.")
        return None


def download_readme(username, repo_name, token):
    readme_url = f'https://api.github.com/repos/{username}/{repo_name}/readme'
    repo_url = f'https://api.github.com/repos/{username}/{repo_name}'
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch README
    readme_response = requests.get(readme_url, headers=headers)

    if readme_response.status_code == 200:
        readme_content = readme_response.json()['content']
        readme_content = base64.b64decode(readme_content).decode('utf-8')

        # Fetch Repository info
        repo_response = requests.get(repo_url, headers=headers)
        if repo_response.status_code == 200:
            last_updated = repo_response.json()['updated_at']
            last_updated = datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%SZ')
            # Convert last_updated to string
            last_updated = last_updated.strftime('%d-%m-%Y %H:%M:%S')
            last_updated += " +0100"

            # Save the README.md file
            with open(os.path.join("data", f"{repo_name}.md"), 'w') as file:
                file.write(readme_content)
            print(f"README.md of the {repo_name} repository downloaded and saved.")
        else:
            print(f"Failed to fetch repository info for {repo_name}. Status code: {repo_response.status_code}")
    else:
        print(f"Failed to fetch README.md for {repo_name}. Status code: {readme_response.status_code}")

    return last_updated


def find_image_references(readme_content):
    # finding image references using regex
    # the image reference should be like ![some_text](image_url)
    image_pattern = re.compile(r'!\[.*?]\((.*?)\)')

    # find all image reference in README file
    image_references = re.findall(image_pattern, readme_content)

    return image_references


def download_images_from_github(image_urls, output_folder):
    # creating output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for img_url in image_urls:
        # getting the image url
        img_name = os.path.basename(img_url)

        # building route to file
        img_destination = os.path.join(output_folder, img_name)

        # download image from GitHub
        response = requests.get(img_url, stream=True)

        if response.status_code == 200:
            with open(img_destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)

            print(f"Image downloaded: {img_url}")
            return True
        else:
            print(f"Error during the download {img_url}")
            return False


def replace_image_path(md_file, old_path, new_path):
    with open(md_file, 'r') as file:
        content = file.read()

    print(f"DEBUG: OLD PATH: {old_path}")

    # new_path = "_posts" + new_path
    # content = re.sub(re.escape(old_path), new_path, content)
    content = str(content).replace(old_path, new_path)

    with open(md_file, 'w') as file:
        file.write(content)

    print(f"old path: {old_path} replaced by new path: {new_path}")


def remove_license_section(md_file):
    with open(md_file, 'r') as file:
        content = file.read()

    # finding the license section
    start_index = content.find("## License")
    end_index = content.find("]", start_index) + 1

    # removing license
    if start_index != -1 and end_index != -1:
        content = content[:start_index] + content[end_index:]

        # saving the updated md file without license
        with open(md_file, 'w') as file:
            file.write(content)

        print("License removed successfully.")
    else:
        print("The current file doesn't have any license.")


def generate_head(file_name, open_ai_api_key):
    print("Contacting OpenAI API...")

    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=open_ai_api_key,
    )

    new_file_name = file_name.replace("md", " ")

    content = open(os.path.join("data", f"{file_name}.md"), "r").read()
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Estrapola dal seguente testo i seguenti campi, e forniscili in formato json:\n\n"
                               "title"
                               "category"
                               "subcategory"
                               "tags"
                               "\nREGOLE CHE DEVI SEGUIRE PER ESTRARRE I CAMPI:\n"
                               "1) Il titolo deve essere uno\n"
                               "2) La categoria deve essere una e deve riferirsi all'argomento generale del testo\n"
                               "3) Le sottocategorie possono essere massimo 2 e devono essere argomenti"
                               " trattati nel testo\n"
                               "4) I tag possono essere massimo 5\n"
                               "5) NON AGGIUNGERE CAMPI CHE NON SONO FRA QUELLI RICHIESTI, e inserisci"
                               " solo categorie, sottocategorie"
                               "e tags che secondo te aiutano il lettore a capire"
                               " di cosa si parla in maniera veloce\n\n"
                               "Testo:"
                               "\n"
                               f"{content}"

                }
            ],
            model="gpt-3.5-turbo-16k",
        )
        json_text = json.loads(chat_completion.choices[0].message.content)
        with open(os.path.join("data", "heading", f"{new_file_name}.json"), "w") as file:
            json.dump(json_text, file, indent=4)
            print(f"File {new_file_name}.json created successfully.")
    except Exception as e:
        print(e)

    # this is forced by the 3 RPM (request per minute) limitation of Open Ai API
    time.sleep(22)


def markdown_heading_builder(json_data, file_name, date):
    with open(json_data, "r") as file:

        json_head = json.load(file)
    try:
        md_head = f"---" \
                  f"\ntitle: {str(json_head['title']).replace(':', ';')}" \
                  f"\ndate: {date}" \
                  f"\ncategory: [{json_head['category']}]" \
                  f"\nsubcategories: [{', '.join(json_head['subcategory'])}]" \
                  f"\ntags: [{', '.join(str(tag.lower()).replace('-', ' ') for tag in json_head['tags'])}]" \
                  "\n---\n\n"
        # TODO add the remaining categories
    except Exception as e:
        print(e)
        md_head = f"---" \
                  f"\ntitle: {str(json_head['title']).replace(':', ';')}" \
                  f"\ndate: {date}" \
                  f"\ncategory: [{json_head['category']}]" \
                  f"\nsubcategories: [{','.join(json_head['subcategories'])}]" \
                  f"\ntags: [{', '.join(str(tag.lower()).replace('-', ' ') for tag in json_head['tags'])}]" \
                  "\n---\n\n"

    content = open(os.path.join("data", f"{file_name}.md"), "r").read()

    # to be tested
    new_content = md_head + content
    new_content = str(new_content).replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"').replace(
        '‘', "'").replace('…', '...').replace('—', '-').replace('–', '-').replace('´', "'")

    tmp_date = datetime.strptime(date, '%d-%m-%Y %H:%M:%S %z')
    date_file_naming = tmp_date.strftime('%Y-%m-%d')

    with open(os.path.join("data", f"{date_file_naming}-{file_name}.md"), "w") as file:
        file.write(new_content)


def gitUploader(dati_utente, md_file):
    # Ottieni un'istanza di GitHub usando il token
    g = Github(dati_utente.get("_Token"))

    sha = None

    repo_name = dati_utente.get("_AccountName") + ".github.io"
    repo = g.get_user().get_repo(repo_name)

    try:
        # Prova a ottenere il contenuto del file <mdfile>.md
        file = repo.get_contents(f"_posts/{md_file}.md")
        sha = file.sha
        print(f"Il file {md_file} esiste su GitHub.")
    except Exception as e:
        # Se il file non esiste, crealo
        if "404" in str(e):
            with open(os.path.join("data", f"{md_file}.md"), "r") as file_content:
                file_content_str = file_content.read()
                repo.create_file(f"_posts/{md_file}.md", "Initial file", file_content_str)
            print(f"File {md_file} creato su GitHub.")

            with open(os.path.join("data", f"{md_file}.md"), "r") as file_content:
                file = repo.get_contents(f"_posts/{md_file}.md")
                sha = file.sha
                file_content_str = file_content.read()
                repo.update_file(f"_posts/{md_file}.md", "automatic update", file_content_str, sha)
                print(f"File {md_file} aggiornato su GitHub.")
                return

    # Se il file esiste, aggiorna il contenuto
    with open(os.path.join("data", f"{md_file}.md"), "r") as file_content:
        file = repo.get_contents(f"_posts/{md_file}.md")
        sha = file.sha
        file_content_str = file_content.read()
        repo.update_file(f"_posts/{md_file}.md", "automatic update", file_content_str, sha)
        print(f"File {md_file} aggiornato su GitHub.")



def startup():
    if not os.path.exists("data"):
        os.mkdir("data")

    __config = os.path.join("data", "config.json")

    if os.path.isfile(__config) and os.access(__config, os.R_OK) and os.path.exists(__config):
        with open(__config, 'r') as config_file:
            user_data = json.load(config_file)
    else:
        while True:
            account_name = input("Your GitHub username: ")
            if is_valid_github_username(account_name):
                break
            else:
                print("The submitted GitHub name doesn't seem valid. Retry.")

        while True:
            github_token = input("Your GitHub access token: ")
            if is_valid_github_token(github_token, f"{account_name}.github.io"):
                break
            else:
                print("TThe submitted GitHub token doesn't seem valid. Retry.")

        open_ai_api_key = input("Your Open AI API key : ")

        user_data = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_OpenAIKey": open_ai_api_key
        }

        with open(__config, "w") as config_file:
            json.dump(user_data, config_file)

    lista_repo = retrieve_repo("softlab-unimore", user_data.get("_Token"))

    with open(os.path.join("data", "lista_repo.json"), "w") as lista_repo_file:
        json.dump(lista_repo, lista_repo_file)

    for repo in lista_repo:
        project_date = download_readme("softlab-unimore", repo, user_data.get("_Token"))
        paths = find_image_references(open(os.path.join("data", f"{repo}.md"), "r").read())
        for image in paths:
            new_path = f"https://raw.githubusercontent.com/softlab-unimore/{repo}/main/{image}"
            if not (download_images_from_github(
                    [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/main/{image}" for image in paths],
                    os.path.join("data", "images"))):
                new_path = f"https://raw.githubusercontent.com/softlab-unimore/{repo}/master/{image}"
                download_images_from_github(
                    [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/master/{image}" for image in paths],
                    os.path.join("data", "images"))

            replace_image_path(os.path.join("data", f"{repo}.md"), image, new_path)
        remove_license_section(os.path.join("data", f"{repo}.md"))
        # generate_head(repo, user_data.get("_OpenAIKey"))
        markdown_heading_builder(os.path.join("data", "heading", f"{repo}.json"), repo, project_date)

        tmp_date = datetime.strptime(project_date, '%d-%m-%Y %H:%M:%S %z')
        date_path = tmp_date.strftime('%Y-%m-%d')

        gitUploader(user_data, f"{date_path}-{repo}")


if __name__ == "__main__":

    # print(chat_completion.choices[0].message.content)

    # drive.mount('/content/drive')
    input_thread = threading.Thread(target=user_input_thread)
    should_exit = False
    first_exec = True
    while not should_exit:
        if first_exec:
            print("Starting...")
            startup()
            first_exec = False
            input_thread.start()
        else:
            time.sleep(20)
            if should_exit:
                break
            else:
                # closing the thread
                startup()
    print("Exited.")

    input_thread.join()
