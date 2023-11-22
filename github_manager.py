from main import *



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
    upd = False

    # Fetch README
    readme_response = requests.get(readme_url, headers=headers)

    if readme_response.status_code == 200:
        readme_content = readme_response.json()['content']
        readme_content = base64.b64decode(readme_content).decode('utf-8')

        # Fetch Repository info
        repo_response = requests.get(repo_url, headers=headers)
        if repo_response.status_code == 200:
            # Save the README.md file
            if os.path.exists(os.path.join("data", f"{repo_name}.md")):
                with open(os.path.join("data", f"{repo_name}.md"), 'r') as old_file:
                    old_content = old_file.read()
                    if old_content != readme_content:
                        upd = True
                        with open(os.path.join("data", f"{repo_name}.md"), 'w') as file:
                            file.write(readme_content)
                            upd = True
                            print(f"README.md of the {repo_name} repository successfullyy updated.")
                    else:
                        print(f"README.md of the {repo_name} repository is up to date.")
            else:
                with open(os.path.join("data", f"{repo_name}.md"), 'w') as file:
                    file.write(readme_content)
                    upd = True
                    print(f"README.md of the {repo_name} repository downloaded and saved.")
        else:
            print(f"Failed to fetch repository info for {repo_name}. Status code: {repo_response.status_code}")
    else:
        print(f"Failed to fetch README.md for {repo_name}. Status code: {readme_response.status_code}")

    return upd


def get_first_commit_date(repo_url, token):
    try:
        # Crea un oggetto GitHub con la tua chiave di accesso o token (se necessario)
        g = Github(token)

        # Ottenere l'oggetto Repository dal suo URL
        repo = g.get_repo(repo_url)

        # Ottieni il primo commit
        first_commit = repo.get_commits()[0]

        # Restituisci la data del primo commit
        return first_commit.commit.author.date.strftime('%d-%m-%Y %H:%M:%S +0100')

    except GithubException as e:
        print(f"Errore durante l'accesso al repository: {e}")
        return None


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


def upload_post(dati_utente, md_file):
    if not md_file.__contains__("SBDIO"):
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
                time.sleep(5)

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



def about_md_creator(dati_utente):
    # se il file about.md non esiste, crealo
    if not os.path.isfile(os.path.join("data", "about.md")):
        with open(os.path.join("data", "about.md"), "w") as file_content:
            file_content_str = "## About\n\n"
            file_content.write(file_content_str)

    # Ottieni un'istanza di GitHub usando il token
    heading = ("---\n"
               "icon: fas fa-info-circle\n"
               "order: 4\n"
               "---\n\n")

    g = Github(dati_utente.get("_Token"))

    sha = None

    repo_name = dati_utente.get("_AccountName") + ".github.io"
    repo = g.get_user().get_repo(repo_name)

    try:
        # Prova a ottenere il contenuto del file about.md
        file = repo.get_contents("_tabs/about.md")
        sha = file.sha
        print(f"Il file about.md esiste su GitHub.")
    except Exception as e:
        # Se il file non esiste, crealo
        if "404" in str(e):
            with open(os.path.join("data", f"about.md"), "r") as file_content:
                file_content_str = file_content.read()
                abt = heading + file_content_str
                repo.create_file("_tabs/about.md", "Initial file", abt)
            print(f"File about.md creato su GitHub.")

            with open(os.path.join("data", f"about.md"), "r") as file_content:
                file = repo.get_contents("_tabs/about.md")
                sha = file.sha
                file_content_str = file_content.read()
                abt = heading + file_content_str
                repo.update_file("_tabs/about.md", "automatic update", abt, sha)
                print(f"File about.md aggiornato su GitHub.")
                return

    # Se il file esiste, aggiorna il contenuto
    with open(os.path.join("data", f"about.md"), "r") as file_content:
        file = repo.get_contents("_tabs/about.md")
        sha = file.sha
        file_content_str = file_content.read()
        abt = heading + file_content_str
        repo.update_file("_tabs/about.md", "automatic update", abt, sha)
        print(f"File about.md aggiornato su GitHub.")



def upload_images(dati_utente, image_name):
    # Ottieni un'istanza di GitHub usando il token
    g = Github(dati_utente.get("_Token"))

    sha = None

    repo_name = dati_utente.get("_AccountName") + ".github.io"
    repo = g.get_user().get_repo(repo_name)

    try:
        # Prova a ottenere il contenuto del file <mdfile>.md
        file = repo.get_contents(f"assets/images/{image_name}")
        sha = file.sha
        print(f"Il file {image_name} esiste su GitHub.")
    except Exception as e:
        # Se il file non esiste, crealo
        if "404" in str(e):
            with open(os.path.join("data", f"images/{image_name}"), "rb") as file_content:
                file_content_str = file_content.read()
                repo.create_file(f"assets/images/{image_name}", "Initial file", file_content_str)
            print(f"File {image_name} creato su GitHub.")

            with open(os.path.join("data", f"images/{image_name}"), "rb") as file_content:
                file = repo.get_contents(f"assets/images/{image_name}")
                sha = file.sha
                file_content_str = file_content.read()
                repo.update_file(f"assets/images/{image_name}", "automatic update", file_content_str, sha)
                print(f"File {image_name} aggiornato su GitHub.")
                return

    # Se il file esiste, aggiorna il contenuto
    with open(os.path.join("data", f"images/{image_name}"), "rb") as file_content:
        file = repo.get_contents(f"assets/images/{image_name}")
        sha = file.sha
        file_content_str = file_content.read()
        repo.update_file(f"assets/images/{image_name}", "automatic update", file_content_str, sha)
        print(f"File {image_name} aggiornato su GitHub.")