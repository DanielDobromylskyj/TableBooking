import os, time
import datetime


class Manager:
    def __init__(self):
        self.numberOfTables = 10

        self.currentLoadedDate = ""
        self.loadedBookings = None
        self.allStudentsBooked = []

    def loadBooking(self, date):
        # Create booking files if needed
        tomorrowsDate = (datetime.datetime.now().date() + datetime.timedelta(days=1))
        if os.path.exists(f"bookings/{tomorrowsDate.strftime('%Y-%m-%d')}.booking") == False:
            if (tomorrowsDate.weekday() != 5) and (tomorrowsDate.weekday() != 6):  # not Sat/Sun
                self.createEmptyBookings(tomorrowsDate.strftime('%Y-%m-%d'))

        todaysDate = datetime.datetime.now().date()
        if os.path.exists(f"bookings/{todaysDate.strftime('%Y-%m-%d')}.booking") == False:
            if (todaysDate.weekday() != 5) and (todaysDate.weekday() != 6):  # not Sat/Sun
                self.createEmptyBookings(todaysDate.strftime('%Y-%m-%d'))

        if date == self.currentLoadedDate:
            return
        else:
            self.save()

        path = f"bookings/{date}.booking"
        if os.path.exists(path):
            self.currentLoadedDate = date
            with open(path, "r") as f:
                fileData = f.read().split("\n")

            table = None
            self.loadedBookings = {
                str(i + 1): {} for i in range(7)
            }

            for chunk in fileData:
                if chunk == "":
                    continue
                op, data = chunk.split(",")

                if op == "META":
                    period, table = data.split("|")
                    self.loadedBookings[period][table] = {
                        "students": [],
                        "booked": False,
                        "bookedBy": " ",
                        "timeBooked": " ",
                        "task": " ",
                        "teacher": " ",
                    }

                elif op == "STUDENT":
                    self.loadedBookings[period][table]["students"].append(data)
                    self.allStudentsBooked.append(data)

                else:
                    self.loadedBookings[period][table][op] = data

        else:
            raise FileNotFoundError

    def studentAlreadyBooked(self, student, period):
        for table in self.loadedBookings[period]:
            if student in self.loadedBookings[period][table]["students"]:
                return True
        return False

    def createEmptyBookings(self, date):
        weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()

        periods = 7
        if (weekday == 0) or (weekday == 4):  # Monday / Friday
            periods = 6

        saveData = ""

        for periodID in range(periods):
            for tableID in range(self.numberOfTables):
                saveData += (f"META,{periodID + 1}|{tableID + 1}\n"
                             f"booked,False\n"
                             f"bookedBy, \n"
                             f"timeBooked,\n"
                             f"task,\n"
                             f"teacher,\n")

        with open(f"bookings/{date}.booking", "w") as f:
            f.write(saveData)

    def tableFree(self, period, table):
        return self.loadedBookings[period][table]["booked"]

    def bookTable(self, period, table, by, students, task, teacher):
        self.loadedBookings[period][table] = {
            "students": students,
            "booked": "True",
            "bookedBy": by,
            "timeBooked": time.strftime("%H:%M %d/%m/%Y"),
            "task": task,
            "teacher": teacher
        }
        self.save()

    def createBooking(self, date: str, period: str, table, by, otherStudents, task, teacher):
        try:
            self.loadBooking(date)
        except:
            return f"No Bookings Available For {date}", 422

        # userData < today-1
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() <= (
                datetime.datetime.now().date() - datetime.timedelta(days=1)):
            return "Please select a current or future date"

        if period.isdigit() == False:
            return "Please select a valid period"

        if (int(period) < 1) or (int(period) > 7):
            return "Please select a valid period"

        if self.studentAlreadyBooked(by, period):
            return f"{by} already has a table booked"

        if len(self.getBookingsFor(by, date)) >= 2:
            return "You already have 2 tables booked today"

        # Check rules against all other students
        for email in otherStudents:
            if email.endswith("@utcncst.org") == False:
                return "Invalid student email"

            if self.studentAlreadyBooked(email, period):
                return "A student is already booked for this period"

            if len(self.getBookingsFor(email, date)) >= 2:
                return "A student already has 2 bookings for today"

            if len(email) > 40:
                return "A student email is too long"

        if self.tableFree(period, table):
            otherStudents.append(by)
            self.bookTable(period, table, by, otherStudents, task, teacher)
            return "You have now booked a table"

        if len(task) > 70:
            return "A student email is too long"

        return "This Table Is Already Taken"

    def getPeriodData(self, date, period):
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() <= (
                datetime.datetime.now().date() - datetime.timedelta(days=1)):
            return {}, 422

        try:
            self.loadBooking(date)
        except:
            return {}, 422

        if (int(period) < 1) or (int(period) > 7):
            return {}, 422

        return {
            str(i + 1): self.loadedBookings[period][str(i + 1)]["booked"] for i in range(self.numberOfTables)
        }

    def getTeacherPeriodData(self, date, period):
        try:
            self.loadBooking(date)
        except:
            return {}, 422
        return self.loadedBookings[str(period)]

    def getBookingsFor(self, student, date):
        try:
            self.loadBooking(date)
        except:
            return {}, 422

        found = []
        for periodID in self.loadedBookings:
            for tableID in self.loadedBookings[periodID]:
                if student in self.loadedBookings[periodID][tableID]["students"]:
                    found.append([periodID, tableID])

        return found

    def save(self):
        saveData = ""

        if self.loadedBookings:
            for periodID in self.loadedBookings:
                for tableID in self.loadedBookings[periodID]:
                    table = self.loadedBookings[periodID][tableID]

                    saveData += (f"META,{periodID}|{tableID}\n"
                                 f"booked,{table['booked']}\n"
                                 f"bookedBy,{table['bookedBy']}\n"
                                 f"timeBooked,{table['timeBooked']}\n"
                                 f"task,{table['task']}\n"
                                 f"teacher,{table['teacher']}\n")

                    for student in table['students']:
                        saveData += f"STUDENT,{student}\n"

            with open(f"bookings/{self.currentLoadedDate}.booking", "w") as f:
                f.write(saveData)

    def SearchDatabase(self, args, delete=False):
        self.save()

        # The Search
        results = []
        validResponses = 0
        for filepath in os.listdir("bookings"):
            date = filepath.split(".booking")[0]

            wantsToSearchThisDate = (args['bookedBefore'] == "*") or (args['bookedBefore'] == "")

            if wantsToSearchThisDate == False:
                wantsToSearchThisDate = (datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.datetime.strptime(args['bookedBefore'],
                                                                '%Y-%m-%d').date())


            if wantsToSearchThisDate:
                self.loadBooking(date)

                for period in self.loadedBookings:
                    if (args['period'] != "") and (args['period'] != "*"):
                        if args['period'] != period:
                            continue

                    for tableID in self.loadedBookings[period]:
                        if (args['table'] != "") and (args['table'] != "*"):
                            if args['table'] != tableID:
                                continue

                        table = self.loadedBookings[period][tableID]

                        if (args['bookedBy'] != "*") and (args['bookedBy'] != table['bookedBy']):
                            continue

                        if (args['bookedFor'] != "*") and (args['bookedFor'] not in table['students']):
                            continue

                        if (args['booked'] == "y") and (table["booked"] != "True"):
                            continue

                        if (args['booked'] == "n") and (table["booked"] == "True"):
                            continue

                        if (args['teacher'] != "*") and (args['teacher'] != table["teacher"]):
                            continue

                        if (args['task'] != "*") and (args['task'] not in table["task"]):
                            continue

                        if delete:
                            if int(args['id']) == validResponses:  # Delete this one
                                self.loadedBookings[period][tableID] = {
                                    "students": [],
                                    "booked": False,
                                    "bookedBy": " ",
                                    "timeBooked": " ",
                                    "task": " ",
                                    "teacher": " ",
                                }
                                self.save()
                                return True

                        results.append(table)
                        results[-1]["period"] = period
                        results[-1]["table"] = tableID

                        validResponses += 1

        if delete:
            return False

        # Return Results
        if args['maxResults'] != "*":
            if len(results) > int(args['maxResults']):
                return results[:int(args['maxResults'])]
        return results

    def DeleteFromDatabase(self, args):
        return {
            "message": str(
                self.SearchDatabase(args, delete=True)
            )
        }