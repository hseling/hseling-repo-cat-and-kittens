import os, sys
import codecs, re
from nltk import sent_tokenize
# import pandas as pd
from collections import Counter
from base64 import b64decode, b64encode
# from flask import Flask, Blueprint, render_template, request, redirect, jsonify
from logging import getLogger
import requests
from flask_mysqldb import MySQL
import json
import re
from flask import *
from hseling_web_cat_and_kittens.file_manager import *
import hseling_web_cat_and_kittens.spelling
import hseling_web_cat_and_kittens.constants as constants
# import secrets
from hseling_web_cat_and_kittens.readability import countFKG, uniqueWords, CEFR

from hseling_web_cat_and_kittens import boilerplate

from sqlalchemy.sql.schema import BLANK_SCHEMA
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
from flask import render_template, request, redirect, url_for, flash
from flask.helpers import make_response
from flask_wtf import form
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_login import current_user
from wtforms import StringField, PasswordField
from wtforms.fields.simple import SubmitField
from wtforms.validators import InputRequired, Email, ValidationError
from wtforms.widgets.core import CheckboxInput
from flask_login import UserMixin
from datetime import datetime


app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('DEBUG', False)
if app.config['DEBUG']:
    print("For debug purposes it's better to use logging module")
app.config['LOG_DIR'] = '/tmp/'
if os.environ.get('HSELING_WEB_CAT_AND_KITTENS_SETTINGS'):
    app.config.from_envvar('HSELING_WEB_CAT_AND_KITTENS_SETTINGS')

app.config['HSELING_API_ENDPOINT'] = os.environ.get('HSELING_API_ENDPOINT')
app.config['HSELING_RPC_ENDPOINT'] = os.environ.get('HSELING_RPC_ENDPOINT')

mysql = MySQL(app)
squlitedb = SQLAlchemy(app)
Login_Manager = LoginManager()
Login_Manager.init_app(app)
Login_Manager.login_view = 'login'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_value')
app.config['SQLALCHEMY_DATABASE_URI'] = 'data/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MYSQL_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_USER'] = os.environ['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DATABASE'] = os.environ['MYSQL_DATABASE']

app.config['TEMPLATES_AUTO_RELOAD'] = True

def get_server_endpoint():
    HSELING_API_ENDPOINT = app.config.get('HSELING_API_ENDPOINT')

    return HSELING_API_ENDPOINT


if not app.debug:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
    file_handler = TimedRotatingFileHandler(os.path.join(app.config['LOG_DIR'], 'hseling_web_cat_and_kittens.log'), 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)


log = getLogger(__name__)

class LoginForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired('Имя пользователя требуется.')])
    password = PasswordField('Password', validators=[InputRequired('Необходим пароль.')])

    def validate_username(self, username):
        user = UserInfo.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('Неверное имя пользователя.')


class RegisterForm(FlaskForm):

    fullname = StringField('ФИО', validators=[InputRequired('Требуется ФИО')])
    username = StringField('Имя пользователя', validators=[InputRequired('Требуется имя пользователя')])
    password = PasswordField('пароль', validators=[InputRequired('Требуется пароль')])
    password1 = PasswordField('Подтвердить пароль', validators=[InputRequired('Подтвердить пароль')])
    email = StringField('Эл. адрес', validators=[InputRequired(), Email(message='Требуется эл. адрес')])

    def validate_username(self, username):
        user = UserInfo.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('A user with this username already exists!')

    def validate_email(self, email):
        email = UserInfo.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('A user with this username already exists!')


class profileForm(FlaskForm):

    fullname = StringField('ФИО', validators=[InputRequired('Требуется ФИО')])
    username = StringField('Имя пользователя', validators=[InputRequired('Требуется имя пользователя')])
    email = StringField('Эл. адрес', validators=[InputRequired(), Email(message='Требуется эл. адрес')])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = UserInfo.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('A user with this username already exists!')

    def validate_email(self, email):
        if email.data != current_user.email:
            email = UserInfo.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('A user with this username already exists!')


class UserInfo(UserMixin, squlitedb.Model):
    id = squlitedb.Column(squlitedb.Integer, primary_key = True)
    account = squlitedb.Column(squlitedb.DateTime, nullable=False, default=datetime.utcnow)
    fullname = squlitedb.Column(squlitedb.String(200))
    username = squlitedb.Column(squlitedb.String(100), unique = True)
    password = squlitedb.Column(squlitedb.String(100))
    email = squlitedb.Column(squlitedb.String(100))
    profileImage = squlitedb.Column(squlitedb.String(20), nullable=False, default='default-profile-pic.jpeg')


    def __init__(self, username, password, email, fullname):
        self.username = username
        self.password = password
        self.email = email
        self.fullname = fullname

    def __repr__(self):
        return self.username


class userUploadForm(squlitedb.Model):
    id = squlitedb.Column(squlitedb.Integer, primary_key = True)
    date_posted = squlitedb.Column(squlitedb.DateTime, nullable=False, default=datetime.utcnow)
    author = squlitedb.Column(squlitedb.String(20), nullable=False)
    content = squlitedb.Column(squlitedb.Text, nullable=False)
    comment = squlitedb.Column(squlitedb.Text, nullable=False)

    def __repr__(self):
        return 'Posted By' + str(self.author)

@Login_Manager.user_loader
def load_user(user_id):
    return UserInfo.query.get(int(user_id))

# ---------------- finish to edit ^^ ----------------------


@app.route('/web/register', methods=['GET','POST'])
def register():
    user = current_user.is_authenticated
    if user:
        return redirect(url_for('profile'))

    registerForm = RegisterForm()

    if registerForm.validate_on_submit():
        if request.form['password'] == request.form['password1']:
            hashPassword = generate_password_hash(registerForm.password.data, method='sha256')
            password = hashPassword
            NewRegister = UserInfo(fullname=registerForm.fullname.data ,username=registerForm.username.data, password=password, email=registerForm.email.data)
            squlitedb.session.add(NewRegister)
            squlitedb.session.commit()
            flash('Registration was successfull')
            return redirect(url_for('login'))

        else:
            flash('Password Dose not Match')
            return redirect(url_for('register'))

    else:
        return render_template('user/register.html', title='register', form=registerForm)

@app.route('/web/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = UserInfo.query.filter_by(username = loginForm.username.data).first()
        if user and check_password_hash(user.password, loginForm.password.data):
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url) if next_url else redirect(url_for('profile'))

        else:
            flash('Неправильный пароль.')
            return redirect(url_for('login'))

    return render_template('user/login.html', title='Login', form=loginForm)


@app.route('/web/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#Image Function For Profile

def saveProfilePicture(picture):
    randomHex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(picture.filename)
    picture_fn = randomHex + f_ext
    picture_path = os.path.join(app.root_path, 'static/media/profile_picture/', picture_fn)
    picture.save(picture_path)
    return picture_fn

@app.route('/web/profile', methods=['GET','POST'])
@login_required
def profile():
    profileUpdateform = profileForm()
    if profileUpdateform.validate_on_submit():
        if profileUpdateform.picture.data:
            picture = saveProfilePicture(profileUpdateform.picture.data)
            current_user.profileImage = picture
        current_user.username = profileUpdateform.username.data
        current_user.email = profileUpdateform.email.data
        current_user.fullname = profileUpdateform.fullname.data
        squlitedb.session.commit()
        flash('Your account is updated!')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        profileUpdateform.fullname.data = current_user.fullname
        profileUpdateform.username.data = current_user.username
        profileUpdateform.email.data = current_user.email

    proImage = url_for('static', filename='media/profile_picture/'+ current_user.profileImage)
    return render_template('user/profile.html', title='profile', proImage=proImage, form=profileUpdateform)


@app.route('/web/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method == 'POST':
        authorUser = request.form['user']
        contentUser = request.form['content']
        commentUser = request.form['comment']
        newContentUpload = userUploadForm(author=authorUser, content=contentUser, comment=commentUser)
        squlitedb.session.add(newContentUpload)
        squlitedb.session.commit()
        flash('Your content is updated!')
        return redirect(url_for('upload'))

    else:
        return render_template('user/upload.html')


@app.route('/web/edit-content/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    editContent = userUploadForm.query.get_or_404(id)
    if request.method == 'POST':
        authorEdit = request.form['user']
        contentEdit = request.form['content']
        commentEdit = request.form['comment']
        newEdit = userUploadForm(author=authorEdit, content=contentEdit, comment=commentEdit)
        squlitedb.session.add(newEdit)
        squlitedb.session.commit()
        flash('Your content is updated!')
        return redirect(url_for('upload'))
    return render_template('user/edit.html', edits=editContent)

@app.route('/web/view-content/<int:id>')
@login_required
def view(id):
    viewContent = userUploadForm.query.get_or_404(id)
    return render_template('user/view.html', views=viewContent)

@app.route('/web/history', methods=['GET','POST'])
@login_required
def history():
    allHistory = userUploadForm.query.order_by(userUploadForm.id).all()
    return render_template('user/history.html', histories=allHistory)

@app.route('/web/')
def index():
    return render_template('index.html', title='Home')

@app.route('/web/search', methods=['GET'])
def search():
    tk = secrets.token_urlsafe()
    session['csrftoken'] = str(tk)
    session_csrftoken = session['csrftoken']
    return render_template('search.html', title='Search', random_token=session_csrftoken)

@app.route('/web/lemma_search', methods=['GET', 'POST'])
def lemma_search():
    if request.method == 'POST':
        details = request.form
        if details['lemma1'] != None or details['lemma2'] != None:
            lemma1 = details['lemma1'] if details['lemma1'] != None else ""
            lemma2 = details['lemma2'] if details['lemma2'] != None else ""
            morph1 = details['morph1'] if details['morph1'] != None else ""
            morph2 = details['morph2'] if details['morph2'] != None else ""
            # syntrole = details['syntax'] if details['syntax'] != "syntrole" else ""
            min_ = details['min'] if details['min'] != None else ""
            max_ = details['max'] if details['max'] != None else ""
            csrftoken = details['csrfmiddlewaretoken']
            if csrftoken == session.get('csrftoken', None):
                print("csrftoken matches")
                api_endpoint = get_server_endpoint() + "/lemma_search?"
                api_endpoint += "&lemma1=" + lemma1
                api_endpoint += "&lemma2=" + lemma2
                api_endpoint += "&morph1=" + morph1
                api_endpoint += "&morph2=" + morph2
                # api_endpoint += "&syntrole=" + syntrole
                api_endpoint += "&min=" + min_
                api_endpoint += "&max=" + max_
                api_endpoint += "&domain=" + details['domain']
                result = requests.get(api_endpoint).content
                return render_template('db_response.html', response=json.dumps(json.loads(result)["values"]), token=lemma1, page="search", display_type="elegant")

            else:
                return "Error 404"
    else:
        return redirect('/web/search')

@app.route('/web/single_token', methods=['GET', 'POST'])
def single_token():
    if request.method == 'POST':
        details = request.form
        print(details)
        if details['search'] != None:
            search_token = details['search'] if details['search'] != None else ""
            csrftoken = details['csrfmiddlewaretoken']
            if csrftoken == session.get('csrftoken', None):
                print("csrftoken matches")
                api_endpoint = get_server_endpoint() + "/single_token_search?token=" + search_token
                api_endpoint += "&domain=" + details['domain']
                result = requests.get(api_endpoint).content
                return render_template('db_response.html', response=json.dumps(json.loads(result)["values"]), token=search_token, page="search", display_type="elegant")
            else:
                return "Error 400"
    else:
        return redirect('/web/search')

@app.route('/web/search_morph')
def search_morph():
    return render_template('search_morph.html', title='Search_morph')

@app.route('/web/base')
def base():
    return render_template('base.html', title='Base')

@app.route('/web/collocations', methods=['GET', 'POST'])
def collocations():

    if request.method == "GET":
        tk = secrets.token_urlsafe()
        session['csrftoken'] = str(tk)
        session_csrftoken = session['csrftoken']
        return render_template('collocations.html', title='Collocations', csrf_token=session_csrftoken)

    else:
        details = request.form
        search_token = details['search_collocations']
        csrftoken = details['csrfmiddlewaretoken']
        if csrftoken == session.get('csrftoken', None):
            print("csrftoken matches")
            search_token = details['search_collocations']
            search_metric = details['search-metric']
            search_metric = boilerplate.metric_converter(search_metric)
            search_domain = details['search-domain']
            search_domain = boilerplate.domain_to_index(search_domain)
            api_endpoint = get_server_endpoint() + "/collocation_search?token=" + search_token + "&metric="
            api_endpoint += search_metric + "&domain=" + str(search_domain)
            result = requests.get(api_endpoint).content
            result = json.loads(result)
            result = result["values"]
            if not result:
                return 'Error 400'
            else:
                return render_template('db_response.html', response=json.dumps(result), token=search_token, page="collocations" , display_type="table")
        else: "Error 400"

#@app.route('/web/upload_file', methods=['GET', 'POST'])
#def upload_file():
#    contents = ''
#    if request.method == 'POST':
#        contents = request.values.get('input_text')
#        requests.post(get_server_endpoint() + 'upload_file', data={"input_text" : contents})
#    return render_template('upload_and_spellcheck.html', text=contents)

@app.route('/web/render_upload_file', methods=['GET'])
def render_upload_file():
    #return render('text')
    return render_template('upload_and_spellcheck.html')



@app.route('/web/upload_text_old', methods=['POST'])
def upload_file():
    print('upload_file', request.json)
    if 'text' in request.json:
        text = request.json['text']
    if not isinstance(text, str):
        text = str(text)
        ##Возможно, стоит возвращать тут серверную ошибку
    if not text.strip():
        return 'Файл не был отправлен', 400
    if not re.search('[А-Яа-яЁё]', text):
        return 'На сайте можно проверять только русскоязычные тексты', 400
    #toDo перед проверкой абзацев избавляться от лишних символов разрыва строки
    if not are_paragraphs_correct(text):
        return 'Разделите длинные абзацы на несколько частей', 400
    else:
        save_file_respond = requests.post(os.path.join(get_server_endpoint(), "upload_text_old"), data={'text': text})
        if save_file_respond.status_code == 200 and 'file_id' in save_file_respond.json():
            return jsonify({'file_id': save_file_respond.json()['file_id']})
        else:
            return 'Произошла непредвиденная ошибка', save_file_respond.status_code



    print('Получили файл, тип объекта', type(file_))
    file_id = save_file_first_time_and_get_id(file_)
    # if not is_encoding_supported(file_id):
    #     return 'Сохраните файл в кодировке utf-8', 400
    # elif not are_paragraphs_correct(file_id):
    #     return 'Разделите длинные абзацы на несколько', 400
    # else:
    return jsonify({'file_id': file_id})

@app.route('/web/get_spelling_problems/<file_id>', methods=['GET'])
def get_spelling_data(file_id):
    text = get_last_version(file_id)
    spellchecker = hseling_web_cat_and_kittens.spelling.SpellChecker()
    problems = spellchecker.check_spelling(text)['problems']
    return jsonify({'spelling_problems': problems})

@app.route('/web/correct_spelling', methods=['POST'])
def correct_spelling():
    file_id = request.json['file_id']
    text = get_last_version(file_id)
    user_corrections = request.json['problems_with_corrections']
    corrected_text = hseling_web_cat_and_kittens.spelling.make_changes(text, user_corrections)
    save_next_version(corrected_text, file_id)
    return jsonify({'success':True})

@app.route('/web/possible_aspects', methods=['GET'])
def possible_aspects():
    ##Переписать функцию, если будут аспекты, которые доступны не всегда
    return jsonify({'possible_aspects': constants.ASPECTS})

@app.route('/web/get_statistics/<file_id>', methods=['GET'])
def get_statistics(file_id):
    text = get_last_version(file_id)
    print(text)
    #text = "Это какой-то текст без ошибок."
    readability_score = countFKG(text)
    total, unique = uniqueWords(text)
    cefr_lvl = CEFR(readability_score)
    return jsonify({'readability_score': readability_score,
                    'total_words': total,
                    'unique_words': unique,
                    'CEFR': cefr_lvl})

@app.route('/web/send_last_version/<file_id>', methods=['GET'])
def send_last_version(file_id):
    text = get_last_version(file_id)
    print('Получен текст', text)
    return jsonify({'text': text})

@app.route('/web/save_edited_text', methods=['POST'])
def save_edited_text():
    data = request.get_json()
    text = data['text']
    file_id = data['file_id']
    save_next_version(text, file_id)
    return jsonify({'success':True})

@app.route('/web/aspects_checking', methods=['POST'])
def aspects_checking():
    data = request.get_json()
    file_id = data['file_id']
    text = get_last_version(file_id)
    aspects = data['chosen_aspects']
    print('web_aspects', aspects)
    #ToDo create route in api and make a query instead of storing api data in web part as we do now
   # if not aspects or not hasattr(aspects, '__iter__') or any([aspect not in constants.ASPECTS for aspect in aspects]):
   #     aspects = constants.ASPECTS
    checker_respond = requests.post(os.path.join(get_server_endpoint(), "check_text"), data={'text': text, 'aspects':'&'.join(aspects)})
    if checker_respond.status_code == 200 and 'problems' in checker_respond.json():
        problems = checker_respond.json()['problems']
    else:
        print('Не удалось получить результаты проверки аспектов')
        problems = {aspect:[] for aspect in aspects}
    return jsonify({'problems':problems, 'text': text})

@app.route('/web/analysis')
def analysis():
    return render_template('analysis.html', title='Analysis')

@app.route('/web/main')
def main():
    return render_template('main.html', title='About us')

@app.route('/web/healthz')
def healthz():
    app.logger.info('Health checked')
    return jsonify({"status": "ok", "message": "hseling-web-cat-and-kittens"})


# @app.route('/web/lol')
# def index():
#     api_endpoint = get_server_endpoint()
#     result = requests.get(api_endpoint).content

#     return render_template('index.html.j2', result=result)


@app.route('/web/test')
def index_test():
    return render_template('index.html.j2', result="This is a string!")


@app.route('/')
def index_redirect():
    return redirect('/web/')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=8000)


__all__ = [app]
