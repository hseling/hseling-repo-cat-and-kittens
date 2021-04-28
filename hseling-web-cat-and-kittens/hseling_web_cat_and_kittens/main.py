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
from hseling_web_cat_and_kittens.readability import countFKG, uniqueWords, CEFR

from hseling_web_cat_and_kittens import boilerplate

from sqlalchemy.sql.schema import BLANK_SCHEMA
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask.helpers import make_response
from flask_wtf import form
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_login import current_user
from wtforms import StringField, PasswordField
from wtforms.fields.simple import SubmitField
from wtforms.validators import InputRequired, Email, ValidationError, Length
from wtforms.widgets.core import CheckboxInput
from flask_login import UserMixin
from datetime import datetime

# Final Import 27/04/2021
# from file_manager import *
# import spelling
# import constants
# from readability import countFKG, uniqueWords, CEFR
from flask_sqlalchemy import *
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import smtplib
from email.message import EmailMessage
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc



app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('DEBUG', False)
if app.config['DEBUG']:
    print("For debug purposes it's better to use logging module")
app.config['LOG_DIR'] = '/tmp/'
if os.environ.get('HSELING_WEB_CAT_AND_KITTENS_SETTINGS'):
    app.config.from_envvar('HSELING_WEB_CAT_AND_KITTENS_SETTINGS')

app.config['HSELING_API_ENDPOINT'] = os.environ.get('HSELING_API_ENDPOINT')
app.config['HSELING_RPC_ENDPOINT'] = os.environ.get('HSELING_RPC_ENDPOINT')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_value')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@database/testdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MYSQL_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_USER'] = os.environ['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DATABASE'] = os.environ['MYSQL_DATABASE']

app.config['TEMPLATES_AUTO_RELOAD'] = True


mysql = MySQL(app)
squlitedb = SQLAlchemy(app)
Login_Manager = LoginManager()
Login_Manager.init_app(app)
Login_Manager.login_view = 'login'

@Login_Manager.user_loader
def load_user(user_id):
    return UserInfo.query.get(int(user_id))

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

# Users Forms
class LoginForm(FlaskForm):

    username = StringField('Имя пользователя', validators=[InputRequired('Имя пользователя требуется.')])
    password = PasswordField('Пароль', validators=[InputRequired('Необходим пароль.'),Length(min=8)])

    def validate_username(self, username):
        user = UserInfo.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('Неверное имя пользователя.')

class passwordChangeForm(FlaskForm):

    password = PasswordField('Новый пароль', validators=[InputRequired('Пожалуйста, введите новый пароль'),Length(min=8)])
    confirmPassword = PasswordField('Введите пароль повторно для подтверждения', validators=[InputRequired('Введите пароль повторно для подтверждения'),Length(min=8)])

class passwordRecoverForm(FlaskForm):

    email = StringField('Введите email', validators=[InputRequired(), Email(message='Пожалуйста, перепроверьте адрес электронной почты')])

    def validate_email(self, email):
        userEmail = UserInfo.query.filter_by(email=email.data).first()
        if userEmail is None:
            raise ValidationError('К вашей электронной почте не привязан личный кабинет. Пожалуйста, зарегистрируйтесь.')

class RegisterForm(FlaskForm):

    fullname = StringField('Полное имя', validators=[InputRequired('Полное имя требуется.')])
    username = StringField('Имя пользователя', validators=[InputRequired('Имя пользователя требуется для.')])
    password = PasswordField('пароль', validators=[InputRequired('пароль требуется для.'),Length(min=8)])
    password1 = PasswordField('Подтвердить пароль', validators=[InputRequired('Подтвердить пароль требуется для.'),Length(min=8)])
    email = StringField('Эл. адрес', validators=[InputRequired(), Email(message='Эл. адрес требуется для.')])

    def validate_username(self, username):
        user = UserInfo.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Пользователь с таким именем уже зарегистрирован.')

    def validate_email(self, email):
        email = UserInfo.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('Введите пароль повторно для подтверждения.')


class profileForm(FlaskForm):

    fullname = StringField('Полное имя', validators=[InputRequired('Полное имя требуется.')])
    username = StringField('Имя пользователя', validators=[InputRequired('Имя пользователя требуется для.')])
    email = StringField('Эл. адрес', validators=[InputRequired(), Email(message='Эл. адрес требуется для.')])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = UserInfo.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Пользователь с таким именем уже зарегистрирован.')

    def validate_email(self, email):
        if email.data != current_user.email:
            email = UserInfo.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('Пользователь с таким адресом электронной почты уже зарегистрирован.')

class historySort(FlaskForm):
    ascending = SubmitField('Дата сохранения')
    descending = SubmitField('Дата сохранения')
    alphabateSort = SubmitField('Комментарий')



# Users Models
class UserInfo(UserMixin, squlitedb.Model):
    id = squlitedb.Column(squlitedb.Integer, primary_key = True)
    account = squlitedb.Column(squlitedb.DateTime, nullable=False, default=datetime.utcnow)
    fullname = squlitedb.Column(squlitedb.String(200))
    username = squlitedb.Column(squlitedb.String(100), unique = True)
    password = squlitedb.Column(squlitedb.String(100))
    email = squlitedb.Column(squlitedb.String(100))
    active = squlitedb.Column(squlitedb.Boolean, unique=False, default=False)
    profileImage = squlitedb.Column(squlitedb.String(200), nullable=False, default='default-profile-pic.jpeg')


    def get_reset_token(self, expires_sec=21600):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id' : self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])

        try:
            user_id = s.loads(token)['user_id']

        except:
            return None

        return UserInfo.query.get(user_id)


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
    version = squlitedb.Column(squlitedb.String(20), nullable=False)
    textid = squlitedb.Column(squlitedb.String(20), nullable=False)
    content = squlitedb.Column(squlitedb.Text, nullable=False)
    comment = squlitedb.Column(squlitedb.Text, nullable=False)
    problems =squlitedb.Column(squlitedb.Text, nullable=True)

    def __repr__(self):
        return 'Posted By' + str(self.author)


class userTextPermmision(squlitedb.Model):
    id = squlitedb.Column(squlitedb.Integer, primary_key = True)
    author = squlitedb.Column(squlitedb.String(20), nullable=False)
    permission = squlitedb.Column(squlitedb.String(20), nullable=False)
    filename = squlitedb.Column(squlitedb.String(50), nullable=False)

    def __repr__(self):
        return 'Posted By' + str(self.author)

# ---------------- finish to edit ^^ ----------------------

# All routes
@app.route('/register', methods=['GET','POST'])
def register():
    registerForm = RegisterForm()

    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    elif registerForm.validate_on_submit():
        if request.form['password'] == request.form['password1']:
            email = registerForm.email.data
            user = registerForm.username.data
            hashPassword = generate_password_hash(registerForm.password.data, method='sha256')
            NewRegister = UserInfo(fullname=registerForm.fullname.data ,username=user, password=hashPassword, email=email)
            squlitedb.session.add(NewRegister)
            squlitedb.session.commit()
            #activation Email Starts
            user1 = UserInfo.query.filter_by(email=email).first()
            token = user1.get_reset_token()
            msg = f'''Hello {user},

Для активации личного кабинета перейдите по ссылке:

{url_for('activeAccount', token=token, _external=True)}

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо. Ссылка действительна в течение 6 часов.
'''
            sendMsg = EmailMessage()
            sendMsg.set_content(msg)

            sendMsg['Subject'] = "пожалуйста, активируйте свой личный кабинет"
            sendMsg['From'] = 'CAT&Kittens'
            sendMsg['To'] = email

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            # server.startssl() # if your website have ssl then you need this
            server.login("Here Will Be Your Email","Here will be your password.")
            server.send_message(sendMsg)
            #activation email ends
            flash('Вы зарегистрированы. Мы отправили вам на почту ссылку для подтверждения регистрации ')
            return redirect(url_for('login'))

        else:
            flash('Пароли не совпадают. ')
            return redirect(url_for('register'))

    else:
        return render_template('user/register.html', title='register', form=registerForm)

@app.route('/active-account/<token>')
def activeAccount(token):
    user = UserInfo.verify_reset_token(token)
    user.active = True
    squlitedb.session.commit()
    return render_template('user/activeAccount.html', title='Active Account', token=str(token))

@app.route('/login', methods=['GET','POST'])
def login():
    loginForm = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    elif loginForm.validate_on_submit():
        user = UserInfo.query.filter_by(username = loginForm.username.data).first()
        if check_password_hash(user.password, loginForm.password.data):
            if user.active:
                if user and check_password_hash(user.password, loginForm.password.data):
                    login_user(user)
                    next_url = request.args.get("next")
                    return redirect(next_url) if next_url else redirect(url_for('profile'))

                else:
                    flash('Неправильный пароль.')
                    return redirect(url_for('login'))
            else:
                flash('Your Account is not activate.')
                return redirect(url_for('login'))

        else:
            flash('Неверный пароль')
            return redirect(url_for('login'))

    return render_template('user/login.html', title='Login', form=loginForm)


@app.route('/logout')
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

@app.route('/profile', methods=['GET','POST'])
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



@app.route('/change-password', methods=['GET','POST'])
@login_required
def changePassword():
    passForm = passwordChangeForm()
    if request.method == 'POST':
        if passForm.validate_on_submit():
            if request.form['password'] == request.form['confirmPassword']:
                hashPassword = generate_password_hash(passForm.password.data, method='sha256')
                current_user.password = hashPassword
                squlitedb.session.commit()
                flash('Пароль успешно изменен')
                logout_user()
                return redirect(url_for('login'))

            else:
                flash('Пароли не совпадают. Повторите попытку')
                return redirect(url_for('changePassword'))

    return render_template('user/changepassword.html', title='Change Password', form=passForm)


# Reset Email Send
def sendResetPasswordEmail(user):
    token = user.get_reset_token()
    msg = f'''Hello {user},

Для сброса пароля перейдите по ссылке:

{url_for('recoverToken', token=token, _external=True)}

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо. Ссылка действительна в течение 6 часов.
'''
    sendMsg = EmailMessage()
    sendMsg.set_content(msg)

    sendMsg['Subject'] = "Here Will Be Your Subject"
    sendMsg['From'] = 'Here will be your website name'
    sendMsg['To'] = user.email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    # server.startssl() # if your website have ssl then you need this
    server.login("Here Will Be Your Email","Here will be your password.")
    server.send_message(sendMsg)


@app.route('/recover-password', methods=['GET','POST'])
def recoverPassword():
    recoverForm = passwordRecoverForm()
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    elif recoverForm.validate_on_submit():
        user = UserInfo.query.filter_by(email=recoverForm.email.data).first()
        sendResetPasswordEmail(user)
        flash('Мы отправили вам письмо с инструкцией по сбросу пароля', 'success')
        return redirect(url_for('login'))

    return render_template('user/recoverpass.html', title='Recover Password', form=recoverForm)


@app.route('/recover-password/<token>', methods=['GET','POST'])
def recoverToken(token):
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    recoverToken = passwordChangeForm()
    if request.method == 'POST':
        user = UserInfo.verify_reset_token(token)
        if current_user.is_authenticated:
            return redirect(url_for('profile'))

        elif recoverToken.validate_on_submit() and user is not None:
            if request.form['password'] == request.form['confirmPassword']:
                hashPassword = generate_password_hash(recoverToken.password.data, method='sha256')
                user.password = hashPassword
                squlitedb.session.commit()
                flash('Пароль успешно обновлен. Вы можете войти в личный кабинет.')
                return redirect(url_for('login'))

            else:
                flash('Password did not match!! Please try again')
                return redirect(url_for('changePassword'))

        else:
            flash('This is an invalid or expired token.', 'warning')
            return redirect(url_for('login'))

    return render_template('user/passwordreset.html', title='Recover Password', form=recoverToken, token=str(token))


@app.route('/edit-content/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    editContent = userUploadForm.query.get_or_404(id)
    if request.method == 'POST':
        authorEdit = request.form['user']
        contentEdit = request.form['content']
        commentEdit = request.form['comment']
        textEdit = request.form['textId']

        checkVersion = userUploadForm.query.all()
        allVersion = []

        for x in checkVersion:
            if x.textid == textEdit:
                allVersion.append(x.version.split('.')[1])
                
        allVersionInt = []
        for x in allVersion:
            allVersionInt.append(int(x))
            
        checkVersionValue = sorted(allVersionInt)

        for x in checkVersionValue:
            try:
                i = 0
                while i < len(checkVersionValue):
                    if checkVersionValue[0] <= checkVersionValue[1]:
                        del(checkVersionValue[0])
                        i += 1
                finalTextVersion = checkVersionValue[-1] + 1

            except:
                finalTextVersion = checkVersionValue[0] + 1

        nextFinalTextVersion = str(textEdit.split('.')[0]) + '.' + str(finalTextVersion)

        delExtraVersion = []
        for x in checkVersion:
            if x.textid == textEdit:
                delExtraVersion.append(x.id)

        if len(delExtraVersion) > 9:
            delEstraVersionDb = userUploadForm.query.get_or_404(delExtraVersion[0])
            squlitedb.session.delete(delEstraVersionDb)
            squlitedb.session.commit()

        newEdit = userUploadForm(
            author = authorEdit,
            content = contentEdit,
            version = nextFinalTextVersion,
            textid = textEdit,
            comment = commentEdit)
        squlitedb.session.add(newEdit)
        squlitedb.session.commit()
        flash('Новая версия текста сохранена.')
        return redirect(url_for('history'))

    return render_template('user/edit.html', edits=editContent)


@app.route('/upload-file', methods=['GET','POST'])
@login_required
def render_upload_file():
    if request.method == 'POST':
        try:
            if request.values['submittext'] == 'uploadTxt':
                spellingFile = request.files['spelling-file']
                finalFile = spellingFile.read(100000)
                fileUser = str(finalFile.decode())
                permissionUser = request.form['permissionUser']
                userName = request.form['user']
                flash('Your Text is Uploaded. Please correct your text then save it for future.')
                return render_template('user/correctfile.html', contentUser=fileUser, permission = permissionUser)

        except:
            if request.values['spellingTxt'] == 'spellingTxt':
                authorUser = request.form['user']
                contentUser = request.form['content']
                commentUser = request.form['comment']
                permissionUser = request.form['permission']
                compairContent = userUploadForm.query.all()
                if compairContent == []:
                    textid = authorUser + 'text1'
                    versionNumber = textid + '.1'

                else:
                    getTotalTextDb = []
                    for x in compairContent:
                        if x.author == authorUser:
                            getTotalTextDb.append(x.textid[len(authorUser + 'text'):])
                    totalText = sorted(getTotalTextDb)
                    try:
                        for y in totalText:
                            i = int(y)
                            while i < len(totalText):
                                if totalText[0] <= totalText[1]:
                                    del(totalText[0])
                        nextTextid = int(totalText[0]) + 1
                        textid = authorUser + 'text' + str(nextTextid)
                        versionNumber = textid + '.1'

                    except:
                        textid = authorUser + 'text' + str(1)
                        versionNumber = textid + '.1'
                    
                    
                newContentUpload = userUploadForm(
                    author = authorUser,
                    content = contentUser,
                    version = versionNumber,
                    textid = textid,
                    comment = commentUser)
                    
                squlitedb.session.add(newContentUpload)
                squlitedb.session.commit()

                userPermissionData = userTextPermmision(
                    author = authorUser,
                    permission = permissionUser,
                    filename = textid)
                squlitedb.session.add(userPermissionData)
                squlitedb.session.commit()
                flash('Новая версия текста сохранена.')
                return redirect(url_for('history'))
    else:
        return render_template('upload_and_spellcheck.html')


@app.route('/delete-content/<int:id>')
@login_required
def delete(id):
    deleteContent = userUploadForm.query.get_or_404(id)
    squlitedb.session.delete(deleteContent)
    squlitedb.session.commit()
    return redirect(url_for('history'))

@app.route('/view-content/<int:id>')
@login_required
def view(id):
    viewContent = userUploadForm.query.get_or_404(id)
    return render_template('user/view.html', views=viewContent)

@app.route('/history', methods=['GET','POST'])
@login_required
def history():
    form = historySort()
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.ascending.data:
                allHistory = userUploadForm.query.order_by(userUploadForm.id)
                return render_template('user/history.html', histories=allHistory, ascending = True, form=form)

            elif form.descending.data:        
                allHistory = userUploadForm.query.order_by(userUploadForm.id.desc())
                return render_template('user/history.html', histories=allHistory, descending=True, form=form)

            elif form.alphabateSort.data:
                    allHistory = userUploadForm.query.order_by(userUploadForm.comment)
                    return render_template('user/history.html', histories=allHistory, descending=True, form=form)

    else:
        allHistory = userUploadForm.query.order_by(userUploadForm.id.desc())
        return render_template('user/history.html', histories=allHistory, descending=True, form=form)


# My Part is done


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
            search_ngrams = details['search-ngrams']
            search_ngrams = boilerplate.ngrams_converter(search_ngrams)
            api_endpoint = get_server_endpoint() + "/collocation_search?token=" + search_token + "&metric="
            api_endpoint += search_metric + "&domain=" + str(search_domain)
            api_endpoint += "&ngrams=" + str(search_ngrams)
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
