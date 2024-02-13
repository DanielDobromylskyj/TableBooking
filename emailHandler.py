import smtplib, ssl

with open("emailPassword.txt", "r") as f:
    password = f.read()

with open("emailName.txt", "r") as f:
    sender_email = f.read()

def SendCode(to, code):
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)  # Secure the connection
        server.login(sender_email, password)

        server.sendmail(sender_email, to, """\
Subject: Verify Your Email

DO NOT SHARE THIS CODE UNDER ANY CONDITIONS, IF SOMEONE IS ASKING YOU FOR IT, THEY ARE LIKELY TRYING TO SCAM YOU.
Code: """ + str(code))
    except Exception as e:
        server = None
        print(e)
    finally:
        if server:
            server.quit()


if __name__ == "__main__":
    SendCode("u21ddobromylskyj@utcncst.org", "4321")