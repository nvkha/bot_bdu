from re import UNICODE
import requests
import dateparser
import datetime
import pytz
import re
import csv
import os
import psycopg2
import psycopg2.extras
from re import T
from bs4 import BeautifulSoup
import tabula


DATABASE_URL = os.environ['DATABASE_URL']

#DB_CONNECTION_STRING = "host=%s dbname=%s user=%s password=%s" % ("localhost", "schedule", "postgres", "810199")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
db = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)


# REGEX
REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"
REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])"
REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"


def getFile(url, name):  
    # Download pdf file from url
    r = requests.get(url, stream=True)

    with open(os.path.join(os.getcwd(), f'{name}.pdf'), 'wb') as f:
        f.write(r.content)
        return name


def pdfToCsv():

    df = tabula.read_pdf("myfile.pdf", encoding='utf-8', pages='all', lattice=True)
    tabula.convert_into("myfile.pdf", "output.csv", output_format="csv", pages='all')
    
    l = ["STT","Thứ","Ngày","Giờ","Số tiết","Phòng","SL","CBGD","Mã MH","Tên môn","Nhóm","Lớp"]
    with open("output.csv", 'r', encoding='utf-8', errors='ignore') as data_file:
        lines = data_file.readlines()
        lines[0]= ",".join(l)+"\n" # replace first line, the "header" with list contents
        with open("output.csv", 'w', encoding='utf-8', errors='ignore') as out_data:
            for line in lines: # write updated lines
                out_data.write(line)

def crawl(name):
    url = "https://camau.bdu.edu.vn/chuyen-muc/sinh-vien/chinh-quy"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    href = ''

    # Tìm link lịch học tuần mới nhất
    for link in soup.find_all('a'):
        if link.get("title"):
            if "Lịch học tuần" in link.get("title"):
                    href = link.get("href")
                    break
    
    # Truy cập link lịch học và download file pdf
    response = requests.get(href)
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all('a'):
        if re.search("pdf$", link.get('href')): 
             getFile(link.get('href'), name)
    pdfToCsv()

def findAndGetSchedule(week_number):
    url = "https://camau.bdu.edu.vn/chuyen-muc/sinh-vien/chinh-quy"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    

    # Tìm link lịch học tuần mới nhất
    for link in soup.find_all('a'):
        if link.get("title"):
            if "Lịch học tuần" in link.get("title"):
                    if int(regex_date(str(link.get('title'))).date().isocalendar()[1]) == week_number:
                        response = requests.get(link.get('href'))
                        soup = BeautifulSoup(response.content, "html.parser")
                        iframe = soup.find('div', {'class': 'td-post-content'}).find('p').find('iframe')
                        id = iframe.get('src').split('/')[-2]
                        URL = f"https://docs.google.com/uc?id={id}&export=download"
                        getFile(URL, 'myfile')
                        pdfToCsv()
                        return True
    return False

findAndGetSchedule(19)

def insert_user(id, class_name):
    db.execute("INSERT INTO users(id, class) VALUES(%s, %s)", (id, class_name))
    conn.commit()


def insert_schedule(id, date_time, room, lecturer, subject, name_class, time, week_number):
        db.execute("INSERT INTO schedule(id, date_time, room, lecturer, subject, class, time, week_number)" 
            "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",(id, date_time, room, lecturer, subject, name_class, time, week_number))
        conn.commit()


def delete_schedule():
    db.execute("DELETE FROM schedule")
    conn.commit()

def save_schedule(filename):
    with open(f"{filename}.csv", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        flag = True
        for row in reader:
            try:
                date = datetime.datetime.strptime(row["Ngày"], '%d/%m/%Y').date()
                if flag == True:
                    week_number = datetime.datetime.strptime(row["Ngày"], '%d/%m/%Y').date().isocalendar()[1]
                    flag = False
                insert_schedule(row["STT"] + str(week_number), date, row["Phòng"], row["CBGD"], row["Tên môn"], row["Lớp"], row["Giờ"], week_number)
            except:
                continue
            
            try:
                db.execute("UPDATE schedule SET class=%s WHERE id=%s", (row[None],row["STT"] + str(week_number)))
                conn.commit()
            except:
                continue
          
    '''
    with open(f"{filename}.csv", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                db.execute("UPDATE schedule SET class=? WHERE id=?", row[None],row["STT"])
            except:
                continue
    ''' 


         

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
        return dateparser.parse(date_str[0], date_formats=['%d-%m-%Y'])

def get_schedule(sender_id, class_name, date=None, week_number=None):       
        dayOfWeek = ["Thứ 2", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        schedule = []

        # Neu co ngay cu the
        if date:
            week = date.isocalendar()[1]
            db.execute("SELECT * FROM schedule WHERE week_number = %s", (week, ))
            rows = db.fetchall()
            if rows:
                for i in rows:
                    if i["date_time"] == date.date() and class_name in i["class"]:
                        schedule.append(i)
            else: 
                if findAndGetSchedule(date.isocalendar()[1]):
                    save_schedule('output')
                    db.execute("SELECT * FROM schedule WHERE date_time=%s AND class LIKE %s", (date.date(),'%'+class_name+'%'))
                    rows = db.fetchall()
                    if rows:
                        schedule = rows
                        
        if week_number:
            week_number = str(week_number)
            db.execute("SELECT * FROM schedule WHERE week_number=%s AND class LIKE %s", (week_number,'%'+class_name+'%'))
            rows = db.fetchall()
            if rows:
                schedule = rows
            else:
                 if findAndGetSchedule(int(week_number)):
                    save_schedule('output')
                    db.execute("SELECT * FROM schedule WHERE week_number = %s AND class LIKE %s", (week_number,'%'+class_name+'%'))
                    rows = db.fetchall()
                    if rows:
                        schedule = rows
                    
        if schedule:
            rows = schedule
            for schedule in rows:
                day = dayOfWeek[schedule['date_time'].isoweekday()]
                send_mess(sender_id, f"Ngày: {schedule['date_time']}\nThứ: {day}\nGiờ: {schedule['time']}\n"
                    f"Phòng: {schedule['room']}")
                    
        else:
            send_mess(sender_id, "Xin lỗi mình không tìm được lịch học của bạn")
        



def send_mess(sender_id, text):
    request_body = {
            'recipient': {
            'id': sender_id
        },
            'message': {"text":text}
        }
    response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+"EAAwf2Q5L720BAImVo7o4NBMS6YDeOlfNRwzvatMX5TUOaVazc8yJ5nekzmvj0cQfI0R1RDyqQ0BKzRmQI8ZAEARAu0On5Evkuc4rcZBMSaQcfyfOMPQv6BVRr7ZCUXw2tu0jm5zHqbKE1Kdd8HKZCR6Nva8QQagJndT0Fn7KwgZDZD",json=request_body).json()
    return response




                         
                    