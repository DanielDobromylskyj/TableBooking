import os.path

import bookingHandler
from datetime import datetime, timedelta

bookings = bookingHandler.Manager()


def desktop(email, name):
    style = """
    <style>
        .headerTitle {
            text-align: center;
            font-size: 50px;
            color: black;
            margin-bottom: 5px;
        }

        .header {
            background-color: purple;
            padding: 10px;
        }

        .box {
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 40%;
            margin: 0 auto;
            margin-top: 20px;
            margin-bottom: 20px;
        }

        body {
            margin: 0px;
            padding: 0px;
            border: 0px;
            background-image: url("https://utcn.s3.amazonaws.com/uploads/home_header/2_6_m.jpg?t=1683110039");
            background-size: cover;
            padding-top: 10%;
            padding-bottom: 10%;
        }

        .booking-day {
            margin-top: 20px;
            text-align: center;
        }

        .date {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .booking-info {
            font-size: 16px;
            margin-bottom: 10px;
        }
    </style>
    """

    # Retrieve bookings
    bookings_info = ""
    for day in range(0, 2):
        booking_date = datetime.now().date() + timedelta(days=day)
        bookings_file = f'bookings/{booking_date}.booking'
        if os.path.exists(bookings_file):
            bookings_for_day = bookings.getBookingsFor(email, booking_date)
            day_info = ""
            for period, table in bookings_for_day:
                day_info += f"<p class='booking-info'>Period {period}, Table {table}</p>"
            if day_info:
                bookings_info += f"<div class='booking-day'><p class='date'>{booking_date}</p>{day_info}</div>"

    if bookings_info == "":
        bookings_info = "<div class='booking-day'><p>You Have No Bookings</p></div>"


    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Viewing {name}'s Bookings</title>
            {style}
        </head>
        <body>
            <div class="box">
                <h2 class="headerTitle">My Bookings</h2>
                <p style="margin: 5px; margin-bottom: 10px">UTCN Library</p>
            </div>
            <div class="box">
                {bookings_info}
            </div>
        </body>
        </html>
        """

def mobile(email, name):
    style = """
    <style>
        .headerTitle {
            text-align: center;
            font-size: 40px;
            color: black;
            margin-bottom: 5px;
        }

        .header {
            background-color: purple;
            padding: 10px;
        }

        .box {
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 80%;
            margin: 0 auto;
            margin-top: 20px;
            margin-bottom: 20px;
        }

        body {
            margin: 0px;
            padding: 0px;
            border: 0px;
            background-image: url("https://utcn.s3.amazonaws.com/uploads/home_header/2_6_m.jpg?t=1683110039");
            background-size: cover;
            padding-top: 10%;
            padding-bottom: 10%;
        }

        .booking-day {
            margin-top: 20px;
            text-align: center;
        }

        .date {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .booking-info {
            font-size: 16px;
            margin-bottom: 10px;
        }
    </style>
    """

    # Retrieve bookings
    bookings_info = ""
    for day in range(0, 2):
        booking_date = datetime.now().date() + timedelta(days=day)
        bookings_file = f'bookings/{booking_date}.booking'
        if os.path.exists(bookings_file):
            bookings_for_day = bookings.getBookingsFor(email, booking_date)
            day_info = ""
            for period, table in bookings_for_day:
                day_info += f"<p class='booking-info'>Period {period}, Table {table}</p>"
            if day_info:
                bookings_info += f"<div class='booking-day'><p class='date'>{booking_date}</p>{day_info}</div>"

    if bookings_info == "":
        bookings_info = "<div class='booking-day'><p>You Have No Bookings</p></div>"


    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Viewing {name}'s Bookings</title>
            {style}
        </head>
        <body>
            <div class="box">
                <h2 class="headerTitle">My Bookings</h2>
                <p style="margin: 5px; margin-bottom: 10px">UTCN Library</p>
            </div>
            <div class="box">
                {bookings_info}
            </div>
        </body>
        </html>
        """
