import os
import sqlite3


def setup():
    print("Welcome to the Table Booking System Setup")
    admins = askAdmins()
    certs = askCert()
    emailInfo = askEmail()

    print("\nCreating Files...")
    createUsers()
    createAdmins(admins)
    createEmail(emailInfo)

    if type(certs) == str:
        print(f"Creating {certs} cert")
        createDummyCert(certs)
    else:
        print("Copies certs")
        createCerts(certs)



def createEmail(info):
    email, password = info

    with open('emailName.txt', "w") as f:
        f.write(email)

    with open('emailPassword.txt', "w") as f:
        f.write(password)

def createDummyCert(certType):
    with open('sslContext.txt', "w") as f:
        f.write(certType)

def createCerts(paths):
    with open('sslContext.txt', "w") as f:
        f.write('certificate.pem\nprivate_key.pem')

    cloneFile(paths[0], 'private_key.pem')
    cloneFile(paths[1], 'certificate.pem')

def cloneFile(src, dst):
    with open(src, 'rb') as f:
        byteData = f.read()

    with open(dst, 'wb') as f:
        f.write(byteData)

def createUsers():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    # Create a table for storing user data
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password_hash TEXT
    )
    ''')

    conn.commit()
    conn.close()


def createAdmins(emails):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    # Create a table for storing user data
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            email TEXT PRIMARY KEY
        )
        ''')
    conn.commit()

    for email in emails:
        email = email.strip()

        if email:  # Ensure the email is not empty
            try:
                c.execute('INSERT INTO teachers (email) VALUES (?)', (email,))
                conn.commit()
            except sqlite3.IntegrityError:
                print(f"Email {email} already exists in the database. Duplicate?")

    conn.close()





def askAdmins():
    print("\nTeachers and Admins")
    emails = []
    while True:
        email = input("Email (or 'stop'):").lower()
        if email == 'stop':
            return emails

        emails.append(email)

def askCert():
    print("\nWebsite Certificates")
    hasCerts = input("Do you have ssl certificates? (y/n)").lower() == 'y'

    if hasCerts:
        privKey = input("Private key path:")
        cert = input("Certificate path:")
        return privKey, cert
    else:
        print("Using adhoc...")
        return 'adhoc'

def askEmail():
    print("\nEmail For Verification")
    print("P.S. This is required for account creation to function")

    return input('email address:'), input('emails \'app\' password:')




if __name__ == "__main__":
    setup()