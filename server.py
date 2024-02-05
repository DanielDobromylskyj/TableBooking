from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
import re
import random
import string

import time

import viewBookings
import emailHandler

import bcrypt

app = Flask(__name__)
app.secret_key = open("secret_key.txt", "r").read()
login_manager = LoginManager()
login_manager.init_app(app)


awaitingVerification = []

with open("users.txt", "r") as f:
    users = {x.split(",")[0]: x.split(",")[1] for x in f.read().split("\n") if x != ""}

with open("admins.txt", "r") as f:
    adminEmails = f.read().split("\n")

def Hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).hex()

def verifyPassword(password, hash):
    return bcrypt.checkpw(password.encode(), bytes.fromhex(hash))


def createAccount(email, password):
    with open("users.txt", "a") as f:
        f.write(f"{email},{password}\n")

    global users
    users[email] = password

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

@app.route('/')
def home():
    with open("static/index.html", "r") as f:
        return f.read()

@app.route('/login', methods=['POST'])
def login():
    args = eval(request.data.decode())

    username = args['username']
    password = args['password']

    # Check if username exists and password is correct
    if username in users and verifyPassword(password, users[username]):
        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for('dashboard'))
    else:
        return "Invalid Email Or Password", 401

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.id in adminEmails:
        with open("static/teacherPortal.html", "r") as f:
            return f.read()

    with open("static/dashboard.html", "r") as f:
        return f.read()

@app.route('/getPeriodOverview', methods=['POST'])
@login_required
def periodOverview():
    if current_user.id in adminEmails:
        return viewBookings.bookings.getTeacherPeriodData(request.json["date"], request.json["period"])
    return {}

def extractName(email):
    return email[3:].split("@")[0]

@app.route('/mybookings')
@login_required
def myBookings():
    return viewBookings.load(
        current_user.id, extractName(current_user.id)
    )


@app.route('/book')
@login_required
def bookATable():
    with open("static/book.html", "r") as f:
        return f.read()


@app.route('/getTableInfo')
@login_required
def checkTablesInfo():
    date, period = request.args["date"], request.args["period"]
    return viewBookings.bookings.getPeriodData(date, period)

@app.route('/CreateBooking', methods=["POST"])
@login_required
def createBooking():
    args = request.json

    r = viewBookings.bookings.createBooking(args["date"], args["period"], args["table"], current_user.id, args["students"], args["taskName"], args["teacher"])
    return {"message": str("Internal Booking System Did Not Respond" if r == None else r)}



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if ("," in email) or ("," in password):
            return 'Comma In Email or Password, Please remove it.'

        # Validate email format and domain
        if not re.match(r'^[a-zA-Z0-9._%+-]+@utcncst\.org$', email):
            return 'Invalid email address. Only email addresses ending with "@utcncst.org" are allowed.'

        if email in users.keys():
            return 'Email already in use.'

        # Generate verification code
        verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        emailHandler.SendCode(email, verification_code)

        awaitingVerification.append({'email': email, 'password': Hash(password), 'verification_code': verification_code, 'time': time.time()})

        # Redirect to a page for email verification
        return redirect(url_for('verify_email'))
    with open('static/register.html', "r") as f:
        return f.read()

@app.route('/verify-email')
def verify_email():
    with open("static/verify_email.html", "r") as f:
        return f.read()

@app.route('/verify-email-code', methods=["POST"])
def verify_email_code():
    code = eval(request.data.decode())["verification_code"]

    for data in awaitingVerification:
        if time.time() - data["time"] > (60*5): # 5 mins
            awaitingVerification.remove(data)
            continue

        if data["verification_code"] == code:
            createAccount(data['email'], data['password'])
            return {"message":"Verified!"}


    return {"message":"Failed To Verify"}




if __name__ == '__main__':
    context = 'adhoc'
    app.run(host="localhost", debug=True, ssl_context=context)
