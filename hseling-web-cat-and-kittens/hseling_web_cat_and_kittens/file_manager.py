from hseling_web_cat_and_kittens import constants
from hseling_web_cat_and_kittens import main
import os
import secrets
import requests
import json


def save_next_version(text, file_id):
    requests.post(os.path.join(main.get_server_endpoint(), "save_next_version_old"), data={"text" : text, "file_id":file_id})

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
    file_system_response = requests.get(os.path.join(main.get_server_endpoint(), 'get_last_version_old/', file_id))
    if file_system_response.status_code == 200 and 'text' in file_system_response.json():
        return file_system_response.json()['text']
    else:
        return ''


def are_paragraphs_correct(text, paragraph_len_limit=10000):
    return all([len(paragraph)<=paragraph_len_limit for paragraph in text.split('\n')])
