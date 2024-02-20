import os


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
    if os.path.exists('users.txt') == False:
        open("users.txt", "w").close()

def createAdmins(emails):
    with open('admins.txt', "w") as f:
        f.write('\n'.join(emails))







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