from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
import re, random, string, secrets, time
import bcrypt

import viewBookings
import emailHandler

# Todo list
# TODO - Advanced Booking Editor - Allow Export To CSV
# TODO - Advanced Booking Editor



app = Flask(__name__)
app.secret_key = secrets.token_hex()

login_manager = LoginManager()
login_manager.init_app(app)


def unauthorized():
    return redirect(url_for('home', sessionExpired=True))


def deviceType(inboundRequest):
    user_agent_string = inboundRequest.user_agent.string
    mobile_pattern = re.compile(r'Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini')
    is_mobile = bool(re.search(mobile_pattern, user_agent_string))

    if is_mobile:
        return 'mobile'
    else:
        return 'desktop'



login_manager.unauthorized_callback = unauthorized

awaitingVerification = []
passwordResetting = {}

with open("users.txt", "r") as fr:
    users = {x.split(",")[0]: x.split(",")[1] for x in fr.read().split("\n") if x != ""}

with open("admins.txt", "r") as fr:
    adminEmails = fr.read().split("\n")


def Hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).hex()


def verifyPassword(password, hash):
    return bcrypt.checkpw(password.encode(), bytes.fromhex(hash))


MIN_PASSWORD_LENGTH = 6
SPECAL_CHARS = list("!\"£$%^&*()_+-={}[]@~:;'#?><,./\\|¬`")


def PasswordSecure(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Password Too Short"

    hasNumber = False
    for char in list(password):
        if char.isdigit():
            hasNumber = True

    if hasNumber == False:
        return "No Numeric Values"

    hasSpecalChar = False
    for char in list(password):
        if char in SPECAL_CHARS:
            hasSpecalChar = True

    if hasSpecalChar == False:
        return "No Special Character"

    return True


def updatePassword(email, password):
    global users
    users[email] = password

    with open("users.txt", "w") as f:
        f.write("\n".join([
            f"{email},{users[email]}" for email in users
        ]) + "\n")


def deleteAccount(email):
    global users
    users.pop(email)

    with open("users.txt", "w") as f:
        f.write("\n".join([
            f"{email},{users[email]}" for email in users
        ]) + "\n")


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
    if username in users and verifyPassword(password, users[username]):
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

        if passwordResetting[auth]['verified'] != True:
            return jsonify({"message": "Failed to change password"}), 422

        if password != confirm:
            return jsonify({"message": "Passwords are not the same"}), 422

        result = PasswordSecure(password)

        if result == True:
            email = passwordResetting[auth]['email']
            updatePassword(email, Hash(password))

            return jsonify({"message": "Complete"}), 200

        else:
            return jsonify({"message": result}), 422


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def deleteMyAccount():
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
    """ Return the respective webpage for the student/teacher dashboard"""
    if current_user.id in adminEmails:
        with open(f"static/{deviceType(request)}/teacherPortal.html", "r") as f:
            return f.read()

    with open(f"static/{deviceType(request)}/dashboard.html", "r") as f:
        return f.read()

@app.route('/advancedDashboard')
@login_required
def advancedDashboard():
    """ Return the respective webpage for the student/teacher dashboard"""
    if current_user.id in adminEmails:
        with open(f"static/{deviceType(request)}/advancedEdit.html", "r") as f:
            return f.read()

@app.route('/searchDB')
@login_required
def searchDB():
    """ Return the respective webpage for the student/teacher dashboard"""
    if current_user.id in adminEmails:
        return viewBookings.bookings.SearchDatabase(request.args)
    return {"message": "You do not have permission to use this api"}

@app.route('/deleteFromDB')
@login_required
def deleteFromDB():
    """ Return the respective webpage for the student/teacher dashboard"""
    if current_user.id in adminEmails:
        return viewBookings.bookings.DeleteFromDatabase(request.args)
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
    if current_user.id in adminEmails:
        return viewBookings.bookings.getTeacherPeriodData(request.json["date"], request.json["period"])
    return {}


def extractName(email):
    try:
        return email[3:].split("@")[0]
    except:
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
    return {"message": str("Internal Booking System Did Not Respond" if r == None else r)}


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

        if (request.json['accept_privacy_policy'] != True):
            return {'message': 'You have not agreed to the privacy policy'}

        if ("," in email):  # We don't need to check in the password as it is stored in HEX (Hashed)
            return {'message': 'Comma in email, Please remove it.'}

        # Validate email format and domain
        if not re.match(r'^[a-zA-Z0-9._%+-]+@utcncst\.org$', email):
            return {'message': 'Invalid email address. Only email addresses ending with "@utcncst.org" are allowed.'}

        # Check for the email in our system
        if email in users.keys():
            return {'message': 'Email already in use.'}

        result = PasswordSecure(password)

        if result == False:
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
    with open(f"static/{deviceType(request)}/verify_email.html", "r") as f:
        return f.read()


@app.route('/verify-email-code', methods=["POST"])
def verify_email_code():
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
    with open(f"static/{deviceType(request)}/privacy_policy.html", "r") as f:
        return f.read()


def getLocalIp():
    import socket

    return socket.gethostbyname(socket.gethostname())


if __name__ == '__main__':
    with open('sslContext.txt', "r") as f:
        context = tuple(f.read().split('\n'))

    if len(context) == 1:
        context = context[0]

    app.run(host=getLocalIp(), port=443, debug=False, ssl_context=context)
