The UTCN Libary Table Booking System allows for tables to be booked online, allowing for students to book a table for a given date and period in the libary.

SET-UP (NOTE - This is no longer required, just run setup.py and follow its instructions and it will do it all for you):

The local ip of the machine running this program must be set on the final line in 'server.py' (replace "localhost" with its local-ip which can be found using 'ipconfig' in a terminal),

Change the values in 'emailName.txt' to be the email you are using,

Create a file called 'emailPassword.txt' and store the email's 'app password' (Not its login password, but it 'app password', you may need to google how to do this),

Create a empty file called 'users.txt',

Create a file called 'admins.txt' and write the teacher(s) email address who will be viewing the bookings (for each teacher, write the email on a new line),

Create a OpenSSL certificate for the website. Store the certs in the following two files 'certificate.pem' and 'private_key.pem'



PLEASE NOTE THE FOLLOWING:

If this is used in a production setting, a production server should be used instead (e.g. production WSGI server)

The python dependancies are not included in this download, The list of required dependancies (not python defaults) are listed:
flask, flask_login, re, bcrypt. 

This program was developed on python 3.9 and may not produce the wanted results on earlier or later versions.

This program was developed and tested on a Windows 11 machine, results may vary on differnet operating systems
