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
from github_manager import *
from ai_operation import *
from common import *
from parsing import *


def user_input_thread():
    global should_exit
    user_input = input("Type \"yes\" to stop: ")
    if user_input == "si" or user_input == "Si" or user_input == "SI" or user_input == "yes" or user_input == "Yes" or \
            user_input == "YES":
        should_exit = True
        print("Quitting...")


def startup():

    build_dir_hierarchy()

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
                print("The submitted GitHub token doesn't seem valid. Retry.")

        open_ai_api_key = input("Your Open AI API key : ")

        user_data = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_OpenAIKey": open_ai_api_key
        }

        with open(__config, "w") as config_file:
            json.dump(user_data, config_file)

    about_md_creator(user_data)

    lista_repo = retrieve_repo("softlab-unimore", user_data.get("_Token"))

    with open(os.path.join("data", "lista_repo.json"), "w") as lista_repo_file:
        json.dump(lista_repo, lista_repo_file)

    for repo in lista_repo:
        if download_readme("softlab-unimore", repo, user_data.get("_Token")):
            project_date = get_first_commit_date(f"softlab-unimore/{repo}", user_data.get("_Token"))
            print(f"PROJECT DATE: {project_date}")
            paths = find_image_references(open(os.path.join("data", f"{repo}.md"), "r").read())
            for image in paths:
                if not image.startswith("http"):
                    new_path = f"/assets/images/{os.path.basename(image)}"
                    if not (download_images_from_github(
                            [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/main/{image}" for image in paths],
                            os.path.join("data", "images"))):
                        download_images_from_github(
                            [f"https://raw.githubusercontent.com/softlab-unimore/{repo}/master/{image}" for image in paths],
                            os.path.join("data", "images"))

                    upload_images(user_data, os.path.basename(image))
                    replace_image_path(os.path.join("data", f"{repo}.md"), os.path.join("data", f"{repo}-edit.md"), image,
                                   new_path)
            remove_license_section(os.path.join("data", f"{repo}-edit.md"), os.path.join("data", f"{repo}.md"))
            ai_form_matter(repo, user_data.get("_OpenAIKey"))
            from_matter_builder(os.path.join("data", "heading", f"{repo}.json"), repo, project_date)

            tmp_date = datetime.strptime(project_date, '%d-%m-%Y %H:%M:%S %z')
            date_path = tmp_date.strftime('%Y-%m-%d')

            upload_post(user_data, f"{date_path}-{repo}")


if __name__ == "__main__":
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
