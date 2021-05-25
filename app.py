import datetime 
from flask import Flask, request
from helper import regex_date, send_mess, get_schedule
import re 
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
db = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)


app = Flask(__name__)

WEBHOOK_VERIFY_TOKEN = 'VERIFY_TOKEN'


@app.route('/')
def hello_world():
    return 'Hello, World!'


# Adds support for GET requests to our webhook
@app.route('/webhook',methods=['GET'])
def webhook():
    verify_token = request.args.get("hub.verify_token")
    # Check if sent token is correct
    if verify_token == WEBHOOK_VERIFY_TOKEN:
        # Responds with the challenge token from the request
        return request.args.get("hub.challenge")
    return 'Unable to authorise.'

# Adds support for POST requests

@app.route("/webhook", methods=['POST'])
def webhook_handle():
    db.execute('CREATE TABLE IF NOT EXISTS users ("id" TEXT primary key, "class" TEXT)')
    conn.commit()
    db.execute('CREATE TABLE IF NOT EXISTS schedule ("id"	INTEGER PRIMARY KEY, "date_time"	DATE, "room"	TEXT, "lecturer"	TEXT, "subject"	TEXT, "class"	TEXT, "time"	TEXT, "week_number"	INTEGER)')
    conn.commit()
    greet = ["hi", "xin chao", "xin chào", "hello", "chao", "chào", 'alo']
    goodbye = ["bye", "goodbye", "tạm biệt", 'tam biet', 'gặp lại sau', 'hẹn gặp lại', 'hen gap lai', 'see you again']
    week = ["lich hoc tuan nay", "tuan nay", "ca tuan", "tuan nay hoc gi", "tuần này",
        "tuan nay hoc gi nhi", "lh", "lịch học tuần này", "tuần này", "cả tuần", "tuan nay học gi", 
        "tuần này học gì", "tuần này học gì nhỉ", "tuần này học gì ku", "tuần nay học gì", "tuan này hoc gi"]
    khen = ["gioi", "được", "thông minh đấy", "cưng quá", "giỏi", "lam tot lam", "làm tốt lắm"]
    thank = ["cảm ơn", "cam on", "thank", "thank you", "cảm ơn em", "cam on em", 
            "cảm ơn mày né", "cam on may nhe", "cảm ơn nha", "cam on nha"]
    next_week = ["tuần sau", "tuần sau học gì",  "tuần sau học gì nhỉ", "tuan sau", "tuan sau hoc gi", "lich hoc tuan sau", "lịch học tuần sau"]

    data = request.get_json()
    
    message = data['message']
    sender_id = data['sender']['id']
    
    db.execute('SELECT * FROM users WHERE id=%s', (sender_id,))
    student = db.fetchall() 
    if not student:
        db.execute("INSERT INTO users(id) VALUES(%s)", (sender_id,))
        conn.commit()

    if message['text'].lower() in greet:
        send_mess(sender_id, "Chào bạn mình là chatbot được thiết kế"
            " để hỏi đáp về lịch học của BDU Cà Mau ạ ^_^")
    elif message['text'].lower() in goodbye:
        send_mess(sender_id, "Hẹn gặp lại bạn <3")
    elif message['text'].lower() in khen:
        send_mess(sender_id, "Cảm ơn bạn nha <3")
    elif message['text'].lower() in thank:
        send_mess(sender_id, "Bạn thiếu nợ mình rồi đó nha hihi")
    elif message['text'].lower() in next_week:
        db.execute('SELECT * FROM users WHERE id=%s', (sender_id,))
        student = db.fetchall()     
        if not student[0]["class"]:
            send_mess(sender_id, "Trước hết hãy cho mình biết bạn học lớp nào nhé ^_^")
            send_mess(sender_id, "Vd: 20TH0101")
        else:
            week_number = datetime.datetime.now().isocalendar()[1]
            get_schedule(sender_id=sender_id, class_name=student[0]["class"].strip("{}"), week_number=week_number + 1)
    elif message['text'].lower() in week:
        db.execute('SELECT * FROM users WHERE id=%s', (sender_id,))
        student = db.fetchall()     
        if not student[0]["class"]:
            send_mess(sender_id, "Trước hết hãy cho mình biết bạn học lớp nào nhé ^_^")
            send_mess(sender_id, "Vd: 20TH0101")
        else:
            week_number = datetime.datetime.now().isocalendar()[1]
            get_schedule(sender_id=sender_id, class_name=student[0]["class"].strip("{}"), week_number=week_number)
    elif regex_date(message['text']):
        db.execute('SELECT * FROM users WHERE id=%s', (sender_id,))
        student = db.fetchall()     
        if not student[0]["class"]:
            send_mess(sender_id, "Trước hết hãy cho mình biết bạn học lớp nào nhé ^_^")
            send_mess(sender_id, "Vd: 20TH0101")
        else:
            date = regex_date(message['text'])
            get_schedule(sender_id=sender_id, class_name=student[0]["class"].strip("{}"), date=date)
    elif re.findall("\d\d\w\w\d\d\d\d", message['text']):
        db.execute("UPDATE users SET class=%s WHERE id=%s", (str(re.findall("\d\d\w\w\d\d\d\d", message['text'])[0]).upper(), sender_id))
        conn.commit()
        send_mess(sender_id, "Chờ mình lưu lại thông tin lớp của bạn trước nha ^_^")
        send_mess(sender_id, "Ok, Bây giờ bạn có thể hỏi mình một số thông tin về lịch học rồi đó ^_^")
    else:
        send_mess(sender_id, "Xin lỗi mình không đủ thông minh để hiểu đước ý của bạn !")
    
    return 'ok'
    
    

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)