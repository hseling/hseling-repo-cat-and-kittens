from hseling_web_cat_and_kittens.constants import UPLOAD_FOLDER

import os
import secrets
import charset_normalizer

def get_txt_path(file_id):
    txt_name = str(file_id) + '.txt'
    return os.path.join(UPLOAD_FOLDER, txt_name)

def save_file_first_time_and_get_id(file):
    print(os.getcwd())
    print(type(file))
    file_id = secrets.token_urlsafe(16)
    print('file_id', file_id)
    file_path = get_txt_path(file_id)
    print('Сохраняем в ' + file_path)
    file.save(file_path)
    print('Сохранили')
    return file_id

def save_next_version(text, file_id):
    with open(get_txt_path(file_id), 'w', encoding='utf-8') as f:
        f.write(text)

def get_last_version(file_id):
    file_name = get_txt_path(file_id)
    print(file_name)
    all_saved_student_texts = os.listdir(UPLOAD_FOLDER)
    if file_name in all_saved_student_texts:
        print('File is found')
        with open(get_txt_path(file_id), encoding='utf-8') as f:
            print('File is open')
            text = f.read()
            return text
    else:
        return ''

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
