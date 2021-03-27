from hseling_web_cat_and_kittens import constants
from hseling_web_cat_and_kittens import main
import os
import secrets
import charset_normalizer
import requests
import json

def get_txt_path(file_id):
    txt_name = str(file_id) + '.txt'
    return os.path.join(txt_name)

def save_file_first_time_and_get_id(file_):
    # print(os.getcwd())
    # print(type(file))
    # file_id = secrets.token_urlsafe(16)
    # print('file_id', file_id)
    # file_path = get_txt_path(file_id)
    # print('Сохраняем в ' + file_path)
    print(file_.read())
    result = requests.post(main.get_server_endpoint() + "/upload", files={"file" : file_.read()})
    print(result.text)
    print(dir(result.raw))
    print(dir(result))
    print(type(result))
    with open(result, 'r') as j:
        data = json.load
    print(result.json())
    # print(result.json())
    # print(type(result))
    # file.save(file_path)
    print('Сохранили')
    return ''
    # return result.json()["file_id"]

def save_next_version(text, file_id):
    with open(get_txt_path(file_id), 'w', encoding='utf-8') as f:
        f.write(text)

# def get_last_version(file_id):
#     file_name = get_txt_path(file_id)
#     print(file_name)
#     all_saved_student_texts = os.listdir(constants.UPLOAD_FOLDER)
#     if file_name in all_saved_student_texts:
#         print('File is found')
#         with open(get_txt_path(file_id), encoding='utf-8') as f:
#             print('File is open')
#             text = f.read()
#             return text
#     else:
#         return ''

def get_last_version(file_id):
    file_name = get_txt_path(file_id)
    print(file_name)
    all_saved_student_texts = requests.get(main.get_server_endpoint() + '/files').content
    print(all_saved_student_texts)
    all_saved_student_texts = json.loads(all_saved_student_texts)["file_ids"]
    print(all_saved_student_texts)
    if file_name in all_saved_student_texts:
        print('File is found')
        text = requests.get(main.get_server_endpoint() + "/files/" + file_name)
        return text
    else:
        return 'Это не текст файла'

def get_encoding(txt_path):
    with open(txt_path, 'rb') as f:
        fileContent = f.read()
    return charset_normalizer.detect(fileContent)['encoding']

def is_encoding_supported(file_id):
    txt_path = get_txt_path(file_id)
    return get_encoding(txt_path) == 'utf_8'

def are_paragraphs_correct(file_id, paragraph_len_limit=10000):
    text = get_last_version(file_id)
    return all([len(paragraph)<=paragraph_len_limit for paragraph in text.split('\n')])
