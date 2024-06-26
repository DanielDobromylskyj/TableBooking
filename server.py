from flask import Flask, request, redirect, url_for, jsonify, send_file
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
import re
import random
import string
import secrets
import time
import bcrypt
import socket
import sqlite3

import viewBookings
import emailHandler

# Todo list
# Todo - tests.py
# Todo - Client testing (?)


app = Flask(__name__)
app.secret_key = secrets.token_hex()

login_manager = LoginManager()
login_manager.init_app(app)


def unauthorized():
    return redirect(url_for('home', sessionExpired=True))


login_manager.unauthorized_callback = unauthorized


def deviceType(inboundRequest):
    user_agent_string = inboundRequest.user_agent.string
    mobile_pattern = re.compile(r'Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini')
    is_mobile = bool(re.search(mobile_pattern, user_agent_string))

    if is_mobile:
        return 'mobile'
    else:
        return 'desktop'


awaitingVerification = []
passwordResetting = {}


def Hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).hex()


def verifyPassword(password, passwordHash):
    return bcrypt.checkpw(password.encode(), bytes.fromhex(passwordHash))


MIN_PASSWORD_LENGTH = 6
SPECIALCHARS = list("!\"£$%^&*()_+-={}[]@~:;'#?><,./\\|¬`")


def PasswordSecure(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Password Too Short"

    containsNumber = False
    for char in list(password):
        if char.isdigit():
            containsNumber = True

    if not containsNumber:
        return "No Numeric Values"

    hasSpecialChar = False
    for char in list(password):
        if char in SPECIALCHARS:
            hasSpecialChar = True

    if not hasSpecialChar:
        return "No Special Character"

    return True


def isAdmin(email):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('SELECT email FROM teachers WHERE email = ?', (email,))
    result = c.fetchone()
    c.close()
    user_database.close()
    return result


def getAccountPasswordHash(email):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    c.close()
    user_database.close()
    return result[0] if result is not None else None


def accountExists(email):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    c.close()
    user_database.close()
    return result is not None


def updatePassword(email, password_hash):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('UPDATE users SET password_hash = ? WHERE email = ?', (password_hash, email))
    user_database.commit()
    c.close()
    user_database.close()


def deleteAccount(email):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('DELETE FROM users WHERE email = ?', (email,))
    user_database.commit()
    c.close()
    user_database.close()


def createAccount(email, hashed_password):
    user_database = sqlite3.connect('user_data.db')
    c = user_database.cursor()
    c.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, hashed_password))
    user_database.commit()
    c.close()
    user_database.close()


class User(UserMixin):
    pass


@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user


@app.route('/', methods=['GET', 'POST'])
def home():
    """ Returns the html code in the static/index.html file """

    with open(f"static/{deviceType(request)}/index.html", "r") as f:
        html = f.read()

        if ('sessionExpired' in request.args) and (request.args['sessionExpired'] == 'True'):
            return html.replace('hidden="hidden"', '')

    return html


@app.route('/login', methods=['POST'])
def login():
    """
    Compare username and password given with the Hashed passwords in our database.
    If valid, create the instance of the user in the system
    """
    args = request.json

    username = args['username'].lower()
    password = args['password']

    # Check if username exists and password is correct
    if accountExists(username) and verifyPassword(password, getAccountPasswordHash(username)):
        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for('dashboard'))
    else:
        return "Invalid Email Or Password", 401


@app.route("/password_reset", methods=["POST", "GET"])
def passwordReset():
    """ Initial Email Confirmation Page For Resetting A Password """

    if request.method == "GET":
        with open(f"static/{deviceType(request)}/reset_password.html", "r") as f:
            return f.read()

    elif request.method == "POST":
        email = request.form["email"]

        if email in users:
            auth = "".join(random.choices(string.ascii_letters + string.digits, k=10))
            code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

            passwordResetting[auth] = {
                "email": email,
                "code": code,
                "attempts": 0,
                "verified": False
            }

            emailHandler.SendCode(email, code)

            return redirect(url_for('verify_password_email', _method="GET", auth=auth))

        else:
            return "An Error Has Occurred During Code Creation"

    else:
        return "Bad Method"


@app.route('/verify_password_email', methods=["POST", "GET"])
def verify_password_email():
    if request.method == "POST":
        code = request.json['code']
        auth = request.json['auth']

        if auth not in passwordResetting:
            return {"message": "Please Give A Valid Code"}, 422

        resetPacket = passwordResetting[auth]

        if resetPacket['attempts'] >= 3:
            return {"message": "Please Give A Valid Code"}, 422
        resetPacket['attempts'] += 1

        if resetPacket['code'] != code:
            return {"message": "Please Give A Valid Code"}, 422

        resetPacket['verified'] = True
        return {"message": "Valid"}, 200

    else:
        with open(f"static/{deviceType(request)}/verify_email_for_password.html", "r") as f:
            return f.read()


@app.route('/new_password', methods=['POST', 'GET'])
def new_password():
    if request.method == 'GET':
        with open(f'static/{deviceType(request)}/new_password.html', 'r') as f:
            return f.read()

    else:
        password = request.json["password"]
        confirm = request.json["confirm"]
        auth = request.json["auth"]

        if auth not in passwordResetting:
            return jsonify({"message": "Failed to change password"}), 422

        if not passwordResetting[auth]['verified']:
            return jsonify({"message": "Failed to change password"}), 422

        if password != confirm:
            return jsonify({"message": "Passwords are not the same"}), 422

        result = PasswordSecure(password)

        if result:
            email = passwordResetting[auth]['email']
            updatePassword(email, Hash(password))

            return jsonify({"message": "Complete"}), 200

        else:
            return jsonify({"message": result}), 422


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def deleteMyAccount():
    """ Deletes a users account from the system, assuming that there password matches the stored hash """
    if request.method == 'GET':
        with open(f"static/{deviceType(request)}/delete.html", "r") as f:
            return f.read()

    else:
        password = request.json['password']

        if verifyPassword(password, users[current_user.id]):
            deleteAccount(current_user.id)

            logout_user()
            return "Deleted", 200

        else:
            return "Invalid Password", 422


@app.route('/dashboard')
@login_required
def dashboard():
    """ Return the respective webpage for the student/teacher dashboard """
    if isAdmin(current_user.id):
        with open(f"static/{deviceType(request)}/teacherPortal.html", "r") as f:
            return f.read()

    with open(f"static/{deviceType(request)}/dashboard.html", "r") as f:
        return f.read()


@app.route('/advancedDashboard')
@login_required
def advancedDashboard():
    """ Returns advanced table booking view webpage if user is a valid teacher """
    if isAdmin(current_user.id):
        with open(f"static/{deviceType(request)}/advancedEdit.html", "r") as f:
            return f.read()


@app.route('/searchDB')
@login_required
def searchDB():
    """ Returns results of a search of all table bookings in the database if authorised by a valid admin / teacher """
    if isAdmin(current_user.id):
        return viewBookings.bookings.SearchDatabase(request.args)
    return {"message": "You do not have permission to use this api"}


@app.route('/deleteFromDB')
@login_required
def deleteFromDB():
    """ Deletes a given booking from the data abase if authorised by a valid admin / teacher """
    if isAdmin(current_user.id):
        return viewBookings.bookings.DeleteFromDatabase(request.args)
    return {"message": "You do not have permission to use this api"}


@app.route('/downloadSearch')
@login_required
def downloadSearch():
    """ Creates a file for downloading that contains table booking information from the last search """
    if isAdmin(current_user.id):
        response = viewBookings.bookings.downloadSearch(request.args)
        if type(response) is str:
            return send_file(response, as_attachment=True)
        else:
            return response
    return {"message": "You do not have permission to use this api"}


@app.route('/account')
@login_required
def account():
    """ Return the webpage for the users account settings """
    with open(f"static/{deviceType(request)}/account.html", "r") as f:
        return f.read().replace("@@@USEREMAIL@@@", current_user.id)


@app.route('/getPeriodOverview', methods=['POST'])
@login_required
def periodOverview():
    """ If a teach, Return all booking data for the given date/period """
    if isAdmin(current_user.id):
        return viewBookings.bookings.getTeacherPeriodData(request.json["date"], request.json["period"])
    return {}


def extractName(email):
    try:
        return email[3:].split("@")[0]
    except IndexError:
        return "Bad Email"


@app.route('/mybookings')
@login_required
def myBookings():
    """ Create a webpage to display the booking data """
    if deviceType(request) == "desktop":
        return viewBookings.desktop(
            current_user.id, extractName(current_user.id)
        )
    else:
        return viewBookings.mobile(
            current_user.id, extractName(current_user.id)
        )


@app.route('/book')
@login_required
def bookATable():
    with open(f"static/{deviceType(request)}/book.html", "r") as f:
        return f.read()


@app.route('/getTableInfo')
@login_required
def checkTablesInfo():
    date, period = request.args["date"], request.args["period"]
    return viewBookings.bookings.getPeriodData(date, period)


@app.route('/CreateBooking', methods=["POST"])
@login_required
def createBooking():
    """ Attempt to create a booking using the booking system,
     returns the response of the booking system """
    args = request.json

    r = viewBookings.bookings.createBooking(args["date"], args["period"], args["table"], current_user.id,
                                            args["students"], args["taskName"], args["teacher"])
    return {"message": str("Internal Booking System Did Not Respond" if r is None else r)}


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    If the method is GET, return the login form page
    If the method is POST, validate the data received from the forms,
    If it is all valid, send a verification email and redirect to the
    code input webpage
    """
    if request.method == 'POST':
        if ('email' not in request.json) or ('password' not in request.json) or ('confirm' not in request.json):
            return {'message': 'Invalid request'}

        email = request.json['email']
        password = request.json['password']
        confirm = request.json['confirm']

        if password != confirm:
            return {'message': 'Passwords do not match'}

        if 'accept_privacy_policy' not in request.json:
            return {'message': 'You have not agreed to the privacy policy'}

        if not request.json['accept_privacy_policy']:
            return {'message': 'You have not agreed to the privacy policy'}

        if "," in email:  # We don't need to check in the password as it is stored in HEX (Hashed)
            return {'message': 'Comma in email, Please remove it.'}

        # Validate email format and domain
        if not re.match(r'^[a-zA-Z0-9._%+-]+@utcncst\.org$', email):
            return {'message': 'Invalid email address. Only email addresses ending with "@utcncst.org" are allowed.'}

        # Check for the email in our system
        if accountExists(email):
            return {'message': 'Email already in use.'}

        result = PasswordSecure(password)

        if not result:
            return {'message': result}

        # Generate verification code
        verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        emailHandler.SendCode(email, verification_code)

        awaitingVerification.append({
            'email': email,
            'password': Hash(password),
            'verification_code': verification_code,
            'time': time.time()
        })

        # Redirect to a page for email verification
        return {'message': 'Complete'}

    with open(f'static/{deviceType(request)}/register.html', "r") as f:
        return f.read()


@app.route('/verify-email')
def verify_email():
    """ Servers the verify-email webpage for a given device"""
    with open(f"static/{deviceType(request)}/verify_email.html", "r") as f:
        return f.read()


@app.route('/verify-email-code', methods=["POST"])
def verify_email_code():
    """ Validates the verification code sent to users email """
    code = request.json["verification_code"]

    for data in awaitingVerification:
        if time.time() - data["time"] > (60 * 5):  # 5 mins
            awaitingVerification.remove(data)
            continue

        if data["verification_code"] == code:
            createAccount(data['email'], data['password'])
            return {"message": "Verified!"}

    return {"message": "Failed To Verify"}


@app.route("/privacy_policy")
def policy():
    """ Servers the privacy-policy webpage """
    with open(f"static/{deviceType(request)}/privacy_policy.html", "r") as f:
        return f.read()


def getLocalIp():
    return socket.gethostbyname(socket.gethostname())


if __name__ == '__main__':
    with open('sslContext.txt', "r") as f:
        context = tuple(f.read().split('\n'))

    if len(context) == 1:
        context = context[0]

    app.run(host=getLocalIp(), port=443, debug=False, ssl_context=context)
