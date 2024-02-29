import requests
import socket

import urllib3

urllib3.disable_warnings()


def getURL():
    return 'https://' + socket.gethostbyname(socket.gethostname()) + ":443"


def testRegister():
    tests = [
        [{  # Fully Valid (Bar email but should pass checks)
            "email": "user@utcncst.org",
            "password": "password",
            "confirm": "password",
            "accept_privacy_policy": True
        }, 'Complete'],

        [{  # Invalid email (bad format)
            "email": "badEmail",
            "password": "password",
            "confirm": "password",
            "accept_privacy_policy": True
        }, 'Invalid email address. Only email addresses ending with "@utcncst.org" are allowed.'],

        [{  # Invalid Domain Name for email
            "email": "badEmail@wrong.domain",
            "password": "password",
            "confirm": "password",
            "accept_privacy_policy": True
        }, 'Invalid email address. Only email addresses ending with "@utcncst.org" are allowed.'],

        [{  # Different passwords
            "email": "user@utcncst.org",
            "password": "password1",
            "confirm": "password2",
            "accept_privacy_policy": True
        }, 'Passwords do not match'],

        [{  # Different passwords
            "email": "user@utcncst.org",
            "password": "password2",
            "confirm": "password1",
            "accept_privacy_policy": True
        }, 'Passwords do not match'],

        [{  # Not Accepted Privacy Policy
            "email": "user@utcncst.org",
            "password": "password",
            "confirm": "password",
            "accept_privacy_policy": False
        }, 'You have not agreed to the privacy policy'],

        [{  # No Privacy Policy
            "email": "user@utcncst.org",
            "password": "password",
            "confirm": "password"
        }, 'You have not agreed to the privacy policy'],

        [{  # No Confirmation Password
            "email": "user@utcncst.org",
            "password": "password",
            "accept_privacy_policy": False
        }, 'Invalid request'],

    ]

    for Json, Response in tests:
        Success = singleRegisterTest(Json, Response)

        if Success != True:
            print("FAILED:\n", Json, '\n', Response)


def singleRegisterTest(validJson, wantedResponse):
    url = getURL() + "/register"

    try:
        r = requests.post(
            url,
            json=validJson,
            verify=False
        ).json()
    except Exception as e:
        print("ERROR:", e)
        return False

    if str(wantedResponse):
        return r['message'] == wantedResponse


def testAll():
    testRegister()


if __name__ == "__main__":
    testAll()
