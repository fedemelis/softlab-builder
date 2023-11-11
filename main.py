import base64
import json
import os
import re
import threading
import time
from urllib.parse import urljoin, urlparse

import openai as openai
import requests as requests
from bs4 import BeautifulSoup
from github import GithubException, Github
from openai import OpenAI


def user_input_thread():
    global should_exit
    user_input = input("Digita \"si\" per uscire: ")
    if user_input == "si" or user_input == "Si" or user_input == "SI" or user_input == "yes" or user_input == "Yes" or user_input == "YES":
        should_exit = True
        print("Quitting...")


def is_valid_github_username(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    return response.status_code == 200


# Verifica l'efficacia di un token GitHub
def is_valid_github_token(token, repository_name):
    try:
        g = Github(token)
        repo = g.get_user().get_repo(repository_name)

        # Prova a creare un file di test
        try:
            repo.create_file("test.txt", "Creating test file", "test content")
        except GithubException as e:
            if e.status == 422 and "sha" in str(e):
                # Ignora l'errore "Invalid request. \"sha\" wasn't supplied."
                pass
            else:
                raise

        # Prova a rimuovere il file di test
        try:
            file = repo.get_contents("test.txt")
            repo.delete_file(file.path, "Removing test file", file.sha)
        except GithubException as e:
            if e.status == 404:
                # Il file non esiste, ma è stato comunque rimosso con successo
                pass
            else:
                raise

        return True
    except Exception as e:
        print(e)
        return False


def retrive_repo(source, pesonal_key):
    url = f"https://api.github.com/users/{source}/repos"
    headers = {"Authorization": f"Bearer {pesonal_key}"}

    risposta = requests.get(url, headers=headers)

    if risposta.status_code == 200:
        repo_pubblici = [repo["name"] for repo in risposta.json()]
        return repo_pubblici
    else:
        print(f"Errore {risposta.status_code}: Impossibile ottenere la lista dei repository pubblici.")
        return None


def download_readme(username, repo_name, token):
    url = f'https://api.github.com/repos/{username}/{repo_name}/readme'
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        readme_content = response.json()['content']
        readme_content = base64.b64decode(readme_content).decode('utf-8')

        # Salva il README.md su disco
        with open(os.path.join("data", f"{repo_name}.md"), 'w', encoding='utf-8') as file:
            file.write(readme_content)
        print(f"README.md per il repository {repo_name} scaricato e salvato.")
    else:
        print(f"Failed to fetch README.md for {repo_name}. Status code: {response.status_code}")


def find_image_references(readme_content):
    # Utilizziamo un'espressione regolare per trovare tutti i riferimenti alle immagini
    # Si suppone che i riferimenti abbiano la forma ![testo_alternativo](url_dell_immagine)
    image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')

    # Trova tutti i riferimenti alle immagini nel README
    image_references = re.findall(image_pattern, readme_content)

    return image_references


def download_images_from_github(image_urls, output_folder):
    # Crea la cartella di output se non esiste già
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for img_url in image_urls:
        # Estrarre il nome del file dall'URL
        img_name = os.path.basename(img_url)

        # Genera il percorso di destinazione
        img_destination = os.path.join(output_folder, img_name)

        # Scarica l'immagine dalla URL di GitHub
        response = requests.get(img_url, stream=True)

        if response.status_code == 200:
            with open(img_destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)

            print(f"Immagine scaricata: {img_url}")
            return True
        else:
            print(f"Errore durante il download dell'immagine {img_url}")
            return False

def replace_image_path(mdFile, old_path, new_path):
    with open(mdFile, 'r', encoding='utf-8') as file:
        content = file.read()

    content = re.sub(re.escape(old_path), new_path, content)

    with open(mdFile, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"Path dell'immagine {old_path} sostituito con {new_path}")


def remove_license_section(mdFile):
    with open(mdFile, 'r', encoding='utf-8') as file:
        content = file.read()

    # Cerca la posizione iniziale e finale della sezione della licenza
    start_index = content.find("## License")
    end_index = content.find("]", start_index) + 1

    # Rimuovi la sezione della licenza
    if start_index != -1 and end_index != -1:
        content = content[:start_index] + content[end_index:]

        # Sovrascrivi il file con il nuovo contenuto
        with open(mdFile, 'w', encoding='utf-8') as file:
            file.write(content)

        print("Sezione della licenza rimossa con successo.")
    else:
        print("Sezione della licenza non trovata.")


def generate_head(file_name, open_ai_api_key):
    print("Richiesta OpenAI in corso...")

    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=open_ai_api_key,
    )

    new_file_name = file_name.replace("md", " ")

    content = open(os.path.join("data", f"{file_name}.md"), "r", encoding="utf-8").read()
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
                               "3) Le sottocategorie possono essere massimo 2 e devono essere argomenti trattati nel testo\n"
                               "4) I tag possono essere massimo 5\n"
                               "5) NON AGGIUNGERE CAMPI CHE NON SONO FRA QUELLI RICHIESTI, e inserisci solo categorie, sottocategorie"
                               "e tags che secondo te aiutano il lettore a capire di cosa si parla in maniera veloce\n\n"
                               "Testo:"
                               "\n\n"
                               f"{content}"

                }
            ],
            model="gpt-3.5-turbo-16k",
        )
        json_text = json.loads(chat_completion.choices[0].message.content)
        with open(os.path.join("data", "heading", f"{new_file_name}.json"), "w", encoding="utf-8") as file:
            json.dump(json_text, file, indent=4)
            print(f"File {new_file_name}.json creato con successo.")
    except Exception as e:
        print(e)

    time.sleep(22)


def markdown_heading_builder(json_data):
    with open(json_data, "r", encoding="utf-8") as file:
        json_head = json.load(file)

    md_head = f"---" \
              f"\ntitle: {json_head['title']}" \
              f"\ncategories: [{json_head['top categoria']},{json_head['']}]" \





def startup():
    if not os.path.exists("data"):
        os.mkdir("data")

    CONFIG = os.path.join("data", "config.json")

    if os.path.isfile(CONFIG) and os.access(CONFIG, os.R_OK) and os.path.exists(CONFIG):
        with open(CONFIG, 'r') as config_file:
            dati_utente = json.load(config_file)
    else:
        while True:
            account_name = input("Inserisci il tuo nome utente di GitHub: ")
            if is_valid_github_username(account_name):
                break
            else:
                print("Nome utente di GitHub non valido. Riprova.")

        while True:
            github_token = input("Inserisci il tuo token di GitHub: ")
            if is_valid_github_token(github_token, f"{account_name}.github.io"):
                break
            else:
                print("Token di GitHub non valido. Riprova.")

        open_ai_api_key = input("Inserisci la tua API key di OpenAI: ")

        dati_utente = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_OpenAIKey": open_ai_api_key
        }

        with open(CONFIG, "w") as config_file:
            json.dump(dati_utente, config_file)

    lista_repo = retrive_repo("softlab-unimore", dati_utente.get("_Token"))

    with open(os.path.join("data", "lista_repo.json"), "w") as lista_repo_file:
        json.dump(lista_repo, lista_repo_file)

    for repo in lista_repo:
        download_readme("softlab-unimore", repo, dati_utente.get("_Token"))
        paths = find_image_references(open(os.path.join("data", f"{repo}.md"), "r", encoding="utf-8").read())
        for image in paths:
            if not (download_images_from_github(
                    [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/main/{image}" for image in paths],
                    os.path.join("data", "images"))):
                download_images_from_github(
                    [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/master/{image}" for image in paths],
                    os.path.join("data", "images"))

            replace_image_path(os.path.join("data", f"{repo}.md"), image, f"images/{os.path.basename(image)}")
        remove_license_section(os.path.join("data", f"{repo}.md"))
        generate_head(repo, dati_utente.get("_OpenAIKey"))
        # markdown_heading_builder(os.path.join("data", "heading", f"{repo}.json"))


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
                # chiudi il thread
                startup()
    print("Exited.")

    input_thread.join()
