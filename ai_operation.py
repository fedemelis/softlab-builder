from main import *

def ai_form_matter(file_name, open_ai_api_key):
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
                               "subcategory [...]"
                               "tags [...]"
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

        # if the heading folder doesn't exist, create it
        if not os.path.exists(os.path.join("data", "heading")):
            os.mkdir(os.path.join("data", "heading"))

        with open(os.path.join("data", "heading", f"{new_file_name}.json"), "w") as file:
            json.dump(json_text, file, indent=4)
            print(f"File {new_file_name}.json created successfully.")
    except Exception as e:
        print("DEBUG: " + str(e))

    # this is forced by the 3 RPM (request per minute) limitation of Open Ai API
    time.sleep(22)