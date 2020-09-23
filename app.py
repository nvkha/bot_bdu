import datetime 
from inspect import getgeneratorlocals
from sqlalchemy import exc 
from flask import Flask, request
from helper import insert_user, regex_date, send_mess, save_schedule
from crawl import crawl, lastestSchedule
from cs50 import SQL 

 


app = Flask(__name__)

WEBHOOK_VERIFY_TOKEN = 'VERIFY_TOKEN'

db = SQL("sqlite:///schedule.db")

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
    greet = ["hi", "xin chao", "xin chào", "hello", "chao", "chào"]
    goodbye = ["bye", "goodbye", "tạm biệt", 'tam biet', 'gặp lại sau', 'hẹn gặp lại', 'hen gap lai', 'see you again']
    week = ["lich hoc tuan nay", "tuan nay", "ca tuan", "tuan nay hoc gi", 
        "tuan nay hoc gi nhi", "lh", "lịch học tuần này", "tuần này", "cả tuần", 
        "tuần này học gì", "tuần này học gì nhỉ", "tuần này học gì ku"]
    
    data = request.get_json()
    event_name = data['event_name']
    if event_name == 'user_send_text':
        message = data['message']
        sender_id = data['sender']['id']
        # Check if student in database 
    student = db.execute('SELECT * FROM users WHERE id=?', sender_id)
    if not student:
        db.execute("INSERT INTO users(id) VALUES(?)", sender_id)

    if message['text'].lower() in greet:
        send_mess(sender_id, "Chào bạn mình là chatbot được thiết kế"
            " để hỏi đáp về lịch học của BDU Cà Mau ạ ^_^")
    elif message['text'].lower() in goodbye:
        send_mess(sender_id, "Hẹn gặp lại bạn <3")
    
    elif message['text'].lower() in week:
        current_schedule = db.execute("SELECT * FROM schedule LIMIT 1")
        week_number_bf = current_schedule[0]["week_number"]
        week_number_cr = datetime.datetime.now().isocalendar()[1]
        if datetime.datetime.now().isoweekday() == 7:
            week_number_cr -= 1
        dayOfWeek = ["Thứ 2", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        
        if week_number_cr > week_number_bf and week_number_cr == lastestSchedule():
            crawl('myfile')
            save_schedule('output')
            rows = db.execute("SELECT * FROM schedule WHERE class LIKE (?)",'%'+student[0]["class"]+'%')
            if rows:
                for schedule in rows:
                    d = datetime.datetime.strptime(schedule['date_time'], '%Y-%m-%d').date().isoweekday()
                    day = dayOfWeek[d]
                    send_mess(sender_id, f"Ngày: {schedule['date_time']}\nThứ: {day}\nGiờ: {schedule['time']}\n"
                        f"Phòng: {schedule['room']}")
        elif week_number_cr == week_number_bf:
            rows = db.execute("SELECT * FROM schedule WHERE class LIKE (?)",'%'+student[0]["class"]+'%')
            if rows:
                for schedule in rows:
                    d = datetime.datetime.strptime(schedule['date_time'], '%Y-%m-%d').date().isoweekday()
                    day = dayOfWeek[d]
                    send_mess(sender_id, f"Ngày: {schedule['date_time']}\nThứ: {day}\nGiờ: {schedule['time']}\n"
                    f"Phòng: {schedule['room']}")
            else:
                send_mess(sender_id, 'Xin lỗi mình không tìm được lịch học của bạn')
        else:
                send_mess(sender_id, 'Xin lỗi mình không tìm được lịch học của bạn')
    elif regex_date(message['text']):
        student = db.execute('SELECT * FROM users WHERE id=?', sender_id)     
        if not student[0]["class"]:
            send_mess(sender_id, "Trước hết hãy cho mình biết bạn học lớp nào nhé ^_^")
            send_mess(sender_id, "Vd: 20TH0101")
        else:
            dayOfWeek = ["Thứ 2", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
            date = regex_date(message['text']).date()
            
            day = dayOfWeek[datetime.datetime.isoweekday(date)]
            week_number_cr = date.isocalendar()[1]
            current_schedule = db.execute("SELECT * FROM schedule LIMIT 1")
            week_number_bf = current_schedule[0]["week_number"]
            if datetime.datetime.now().isoweekday() == 7:
                week_number_cr -= 1 

            if week_number_cr == week_number_bf:
                rows = db.execute("SELECT * FROM schedule WHERE date_time = ? AND class LIKE (?)", date,'%'+student[0]["class"]+'%')
                if rows:
                    for schedule in rows:
                        send_mess(sender_id, f"Ngày: {date}\nThứ: {day}\nGiờ: {schedule['time']}\n"
                            f"Phòng: {schedule['room']}")
                else:
                    send_mess(sender_id, 'Xin lỗi mình không tìm được lịch học của bạn')
            elif week_number_cr > week_number_bf and week_number_cr == lastestSchedule():
               crawl('myfile')
               save_schedule('output')
               rows = db.execute("SELECT * FROM schedule WHERE date_time = ? AND class LIKE (?)", date,'%'+student[0]["class"]+'%') 
               if rows:
                    for schedule in rows:
                        send_mess(sender_id, f"Ngày: {date}\nThứ: {day}\nGiờ: {schedule['time']}\n"
                            f"Phòng: {schedule['room']}")
               else: 
                    send_mess(sender_id, 'Xin lỗi mình không tìm được lịch học của bạn')
            else:
                send_mess(sender_id, 'Xin lỗi mình không tìm được lịch học của bạn')

    elif message['text'][-4:] == "0101":
        db.execute("UPDATE users SET class=?", message['text'])
        send_mess(sender_id, "Bây giờ bạn có thể hỏi mình một số thông tin về lịch học rồi đó ^_^")
    else:
        send_mess(sender_id, "Xin lỗi mình không đủ thông minh để hiểu đước ý của bạn !")

    return 'ok'
    
    

if __name__ == "__main__":
    app.run(threaded=True, port=5000)