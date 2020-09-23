from re import UNICODE
from flask import request
import requests
from cs50 import SQL
import dateparser
import datetime
import pytz
import re
import csv

# REGEX
REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"
REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])"
REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///schedule.db")

def insert_user(id):
    student = ("SELECT * FROM users WHERE id=?", id)
    if student:
        return Flase
    else: 
        db.execute("INSERT INTO users VALUES(?, ?)", id)

def getStudent(id):
    student = ("SELECT * FROM users WHERE id=?", id)
    if student:
        return student
    else: 
        db.execute("INSERT INTO users VALUES(?, ?)", id, name_class)

def insert_schedule(id, date_time, room, lecturer, subject, name_class, time, week_number):
        db.execute("INSERT INTO schedule(id, date_time, room, lecturer, subject, class, time, week_number)" 
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",id, date_time, room, lecturer, subject, name_class, time, week_number)


def delete_schedule():
    db.execute("DELETE FROM schedule")

def save_schedule(filename):
    delete_schedule()
    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        flag = True
        for row in reader:
            try:
                date = datetime.datetime.strptime(row["Ngày"], '%d/%m/%Y').date()
                if flag == True:
                    week_number = datetime.datetime.strptime(row["Ngày"], '%d/%m/%Y').date().isocalendar()[1]
                    flag = False
                insert_schedule(row["STT"],date, row["Phòng"], row["CBGD"], row["Tên môn"], row["Lớp"], row["Giờ"], week_number)
            except:
                continue
    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                db.execute("UPDATE schedule SET class=? WHERE id=?", row[None],row["STT"])
            except:
                continue


         

def regex_date(msg, timezone="Asia/Ho_Chi_Minh"):
    ''' use regex to capture date string format '''

    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz)
    temp = msg

    date_str = []
    regex = REGEX_DATE
    regex_day_month = REGEX_DAY_MONTH
    regex_month_year = REGEX_MONTH_YEAR
    pattern = re.compile("(%s|%s|%s)" % (
        regex, regex_month_year, regex_day_month), re.UNICODE)

    matches = pattern.finditer(msg)
    for match in matches:
        _dt = match.group(0)
        _dt = _dt.replace("/", "-").replace("|", "-").replace(":", "-")
        for i in range(len(_dt.split("-"))):
            if len(_dt.split("-")[i]) == 1:
                _dt = _dt.replace(_dt.split("-")[i], "0"+_dt.split("-")[i])
        if len(_dt.split("-")) == 2:
            pos1 = _dt.split("-")[0]
            pos2 = _dt.split("-")[1]
            if 0 < int(pos1) < 32 and 0 < int(pos2) < 13:
                _dt = pos1+"-"+pos2+"-"+str(now.year)
        date_str.append(_dt)
    if not date_str: 
        lst = ["hôm qua", "hôm nay", "ngày mai"]
        temp = temp.replace("mai", "ngày mai")
        temp = temp.replace("qua", "hôm qua")
        temp = temp.replace("mơi", "ngày mai")
        temp = temp.replace("nay", "hôm nay")
        temp = temp.replace("bữa nay", "hôm nay")
        for word in lst:
            if re.findall(word, temp):
                date_str.append(re.findall(word, temp))
                date_str = dateparser.parse(date_str[0][0])
        return date_str
    else:
        return dateparser.parse(date_str[0])

def send_mess(sender_id, text):
    request_body = {
            'recipient': {
            'user_id': sender_id
        },
            'message': {"text":text}
        }
    response = requests.post("https://openapi.zalo.me/v2.0/oa/message?access_token=-D2JPkhkbolxrv9fx-kOAVxGb6pnY91I_ThxJPFYW5phZSLXZCcS9P-3msF6_Q1cZvtnLiEZdqxIpPLxlOZkIFdla6MeeDH5_UpSNfIzZ5Z5rCD_W9gPJfBpqGY7hQT8tiVUIxEVi0kchFyKwCYfKFYXfdIxxyetqOsI2hl2wHJFefOflvZw9_QZyoJYmxuOzxop69ZpsIhmZh0ljEEy2jdUjp-ffUWlm--2QeIbxcRpxBLHge7JQi7lrckDljrLv_dMVe-hsLljvPTPdDVD6j25nmEtwSv3Jo4BF7JgzPOW",json=request_body).json()
    return response




                         
                    