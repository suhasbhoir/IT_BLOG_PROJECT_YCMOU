from flask import Flask, render_template, request, session, redirect, flash, url_for
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from flask_bootstrap import Bootstrap
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, SubmitField
# from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from datetime import datetime
from flask_mail import Mail, Message
import json, os, math, email_validator
from flask_bcrypt import Bcrypt
# from flaskext.mysql import MySQL
import mysql.connector
from random import randint

with open("openconfig.json", 'r') as wt:
    para = json.load(wt)["parameters"]
local_server = True
app = Flask(__name__)
app.secret_key = os.urandom(128)  # 'super-secret-key'
app.config['UPLOAD_FOLDER'] = para['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=para['mail_user'],
    MAIL_PASSWORD=para['mail_pass']
)
mail = Mail(app)
otp = randint(000000, 999999)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = para['local_server_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = para['prod_server_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
conn = mysql.connector.connect(user="suhasbhoir",
                               password="xswqazZX2$",
                               database="networkthunder",
                               host="localhost")
cursor = conn.cursor()


# mysql = MySQL()
# app.config['MYSQL_DATABASE_USER'] = para['mysql_cred']
# app.config['MYSQL_DATABASE_PASSWORD'] = para['mysql_cred']
# app.config['MYSQL_DATABASE_DB'] = para['mysql_cred']
# app.config['MYSQL_DATABASE_HOST'] = para['mysql_cred']
# mysql.init_app(app)


class Contacts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


class User(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), unique=True, nullable=False)


# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(25), unique=False)
#     username = db.Column(db.String(15), unique=True)
#     email = db.Column(db.String(50), unique=True)
#     password = db.Column(db.String(80))
#
#
# class RegisterForm(FlaskForm):
#     username = StringField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder": "username"})
#     password = PasswordField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder": "password"})
#
#     submit = SubmitField('Register')
#
#     def validate_username(self, username):
#         existing_user_username = User.query.filter_by(username=username.data).first()
#
#         if existing_user_username:
#             raise ValidationError("username exist")
#
# class LoginForm(FlaskForm):
#     username = StringField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder": "username"})
#     password = PasswordField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder": "password"})
#
#     submit = SubmitField('Login')


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(para['no_of_post']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(para['no_of_post']):(page - 1) * int(para['no_of_post']) + int(
        para['no_of_post'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', parameters=para, posts=posts, prev=prev, next=next)


@app.route("/about/")
def about():
    return render_template('about.html', parameters=para)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', parameters=para, post=post)


@app.route("/contact/", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message for NetworkThunder Blog', sender=email,
                          recipients=[para['mail_user']],
                          body=message + "\n" + phone)
        flash("Your contact details have been sent successfully to the blog admin ", "success")
    return render_template('contact.html', parameters=para)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if "user" in session and session['user'] == para['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", parameters=para, posts=posts)

    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if username == para['admin_user'] and userpass == para['admin_password']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", parameters=para, posts=posts)
        elif username != para['admin_user'] or userpass != para['admin_password']:
            return render_template("admin_login_fail.html", parameters=para)

    else:
        return render_template("login.html", parameters=para)


@app.route("/userdashboard", methods=['GET', 'POST'])
def userdashboard():
    if "user_id" in session:
        posts = Posts.query.all()
        return render_template("userDash.html", parameters=para, posts=posts)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        cursor.execute(
            "SELECT * FROM `user` WHERE `username` LIKE '{}' AND `password` LIKE '{}' ".format(username, password))
        users = cursor.fetchall()
        # print(users)
        if len(users) > 0:
            print(users)
            session['user_id'] = users[0][0]
            posts = Posts.query.all()
            return render_template("userDash.html", parameters=para, posts=posts)
        elif 'user_id' != session:
            return render_template("admin_login_fail.html", parameters=para)

    else:
        return render_template("login.html", parameters=para)


# @app.route("abc")
# def abc():
#     return render_template("userDash.html")


@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):
    if "user" in session and session['user'] == para['admin_user']:
        if request.method == "POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if srno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + srno)

        post = Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html', parameters=para, post=post, srno=srno)


@app.route("/edit1/<string:srno>", methods=['GET', 'POST'])
def edit1(srno):
    if "user_id" in session:
        if request.method == "POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if srno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit1/' + srno)

        post = Posts.query.filter_by(srno=srno).first()
        return render_template('edit1.html', parameters=para, post=post, srno=srno)


@app.route("/uploader/", methods=['GET', 'POST'])
def uploader():
    if "user" in session and session['user'] == para['admin_user']:
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return render_template('fus.html', parameters=para)
    else:
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return render_template('fus.html', parameters=para)



@app.route("/logout/")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/logout1/")
def logout1():
    session.pop('user_id')
    return redirect('/userlogin')


@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):
    if "user" in session and session['user'] == para['admin_user']:
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


# _________________________________________________________________
@app.route("/userlogin", methods=['GET', 'POST'])
def userlogin():
    username = request.form.get('username')
    password = request.form.get('password')

    if request.method == 'POST':
        usnm = request.form["username"]
        session["user"] = usnm
        print(usnm)

    cursor.execute(
        "SELECT * FROM `user` WHERE `username` LIKE '{}' AND `password` LIKE '{}' ".format(username, password))
    users = cursor.fetchall()
    # print(users)
    if len(users) > 0:
        print(users)
        session['user_id'] = users[0][0]
        return redirect('/userdashboard')

    else:
        return render_template('userlogin.html', )

#
# @app.route("/<uuid>")
# def uuid(usr):
#     return f"<h1>{usr}</h1>"

@app.route("/registeruser", methods=['GET', 'POST'])
def registeruser():
    return render_template('signup.html', parameters=para)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        '''Add entry to the database'''
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        msg = Message(subject='OTP', sender=para['mail_user'], recipients=[email])
        msg.body = str(otp)
        mail.send(msg)
        phone = request.form.get('phone')
        password = request.form.get('password')
        entry1 = User(name=name, username=username, password=password, date=datetime.now(), email=email)
        db.session.add(entry1)
        db.session.commit()
        return render_template('otpsent.html', parameters=para)

    else:
        username = request.form.get('username')
        cursor.execute("""SELECT * FROM `user` WHERE `username` LIKE '{}'""".format(username))
        newuser = cursor.fetchall()
        session['user_id'] = newuser[0][0]
        return redirect('/userlogin')

    # return render_template('userlogin.html', parameters=para)

@app.route('/otpvalidate', methods=['POST'])
def otpvalidate():
    user_otp = request.form['otp']
    if otp == int(user_otp):
        flash("Your Email verification successful ", "success")
        return render_template('userlogin.html', parameters=para)
    else:
        flash("Authentication to OTP failed", "critical")
        return render_template('otpsent.html', parameters=para )


    # null = 'NULL'
    # name = request.form.get('name')
    # date = 'CURRENT_TIMESTAMP'
    # username = request.form.get('username')
    # email = request.form.get('email')
    # password = request.form.get('password')
    #
    # """INSERT INTO `user` (`id`, `name`, `date`, `username`, `email`, `password`) VALUES (NULL, 'Pramod mane', CURRENT_TIMESTAMP, 'pramod1988', 'pramod@gmail.com', 'zxc_123');"""
    # cursor.execute("""INSER INTO `user` (`id`, `name`, `date`, `username`, `email`, `password`) VALUES ('{}','{}','{}','{}','{}','{}')""".format(null, name, date, username, email, password))
    # print(cursor.execute("INSER INTO `user` (`id`, `name`, `date`, `username`, `email`, `password`) VALUES ('{}','{}','{}','{}','{}','{}')".format(null, name, date, username, email, password)))
    # conn.commit()
    # return "<h1>User added to db<h1>"

    # form = RegisterForm()
    # if form.validate_on_submit():
    #     hashpass = Bcrypt.generate_password_hash(form.password.data)
    #     new_user = User(username=form.username.data, password=hashpass)
    #     db.session.add(new_user)
    #     db.session.commit()
    #     return redirect(url_for('userlogin'))
    # return render_template('signup.html', form=form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
