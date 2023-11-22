from main import *


def find_image_references(readme_content):
    # finding image references using regex
    # the image reference should be like ![some_text](image_url)
    image_pattern = re.compile(r'!\[.*?]\((.*?)\)')

    # find all image reference in README file
    image_references = re.findall(image_pattern, readme_content)

    return image_references


def replace_image_path(md_file, edited_md_file, old_path, new_path):
    with open(md_file, 'r') as file:
        content = file.read()

    print(f"DEBUG: OLD PATH: {old_path}")

    # new_path = "_posts" + new_path
    # content = re.sub(re.escape(old_path), new_path, content)
    content = str(content).replace(old_path, new_path)

    with open(edited_md_file, 'w') as file:
        file.write(content)

    print(f"old path: {old_path} replaced by new path: {new_path}")


def remove_license_section(md_file, original_md_file):
    if not os.path.exists(md_file):
        with open(original_md_file, 'r') as file:
            content = file.read()
            with open(md_file, 'w') as file:
                file.write(content)

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


def from_matter_builder(json_data, file_name, date):
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
    except Exception as e:
        print(e)
        md_head = f"---" \
                  f"\ntitle: {str(json_head['title']).replace(':', ';')}" \
                  f"\ndate: {date}" \
                  f"\ncategory: [{json_head['category']}]" \
                  f"\nsubcategories: [{','.join(json_head['subcategories'])}]" \
                  f"\ntags: [{', '.join(str(tag.lower()).replace('-', ' ') for tag in json_head['tags'])}]" \
                  "\n---\n\n"

    content = open(os.path.join("data", f"{file_name}-edit.md"), "r").read()

    # to be tested
    new_content = md_head + content
    new_content = str(new_content).replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"').replace(
        '‘', "'").replace('…', '...').replace('—', '-').replace('–', '-').replace('´', "'")

    tmp_date = datetime.strptime(date, '%d-%m-%Y %H:%M:%S %z')
    date_file_naming = tmp_date.strftime('%Y-%m-%d')

    with open(os.path.join("data", f"{date_file_naming}-{file_name}.md"), "w") as file:
        file.write(new_content)
