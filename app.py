import re
from pymongo import MongoClient
import pymysql
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


connect = pymysql.connect(host='localhost', port=3306, user='root', password='1234', db='dblogin', charset='utf8') 
cursor = connect.cursor(pymysql.cursors.DictCursor)


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('localhost', 27017, username="test", password="test")
db = client.dblogin


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # Client info 보내주기
        # user_info = db.users.find_one({"username": payload["id"]})
        
        sql = "SELECT * FROM users where username = '%s';"
        cursor.execute(sql%(payload["id"]))
        result = cursor.fetchone()

        return render_template('index.html', user_info=result)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        # user_info = db.users.find_one({"username": username}, {"_id": False})
        
        sql = "SELECT * FROM users where username = '%s';"
        cursor.execute(sql%(username))
        result = cursor.fetchone()

        return render_template('user.html', user_info=result, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# Login Sever
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    # result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    sql = "SELECT username, password FROM users"
    cursor.execute(sql)
    loginResult = cursor.fetchall()
    loginResultCount = loginResult.count({'username': username_receive, 'password': pw_hash})

    if loginResultCount == 1:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 회원가입 Server
@app.route('/sign_up/save', methods=['POST'])
def sign_up():

    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }


    sql = "insert into users(username, password, profile_name, profile_pic_real,profile_pic,profile_info) values(%s, %s, %s, 'profile_pics/profile_placeholder.png',"","")"

    cursor.execute(sql,(username_receive,password_hash,username_receive))
    connect.commit()

    # db.users.insert_one(doc)

    return jsonify({'result': 'success'})

# id 중복확인 Server
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    # exists = bool(db.users.find_one({"username": username_receive}))
    sql = "SELECT * FROM users where username = '%s';"
    cursor.execute(sql%(username_receive))
    result = bool(cursor.fetchone())
    

    
    return jsonify({'result': 'success', 'exists': result})

# Profile 수정 Server
@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/"+file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set':new_doc})


        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# @app.route('/posting', methods=['POST'])
# def posting():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

#         # Posting API
#         user_info = db.users.find_one({"username": payload["id"]})


#         comment_receive = request.form["comment_give"]
#         date_receive = request.form["date_give"]

#         doc = {
#             "username": user_info["username"],
#             "profile_name": user_info["profile_name"],
#             "profile_pic_real": user_info["profile_pic_real"],
#             "comment": comment_receive,
#             "date": date_receive
#         }

#         db.posts.insert_one(doc)

#         return jsonify({"result": "success", 'msg': '포스팅 성공'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route("/get_posts", methods=['GET'])
# def get_posts():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

#         # 서버 if문 & 문자열로 변환하기
#         username_receive = request.args.get("username_give")
#         if username_receive == "":
#             posts = list(db.posts.find({}).sort("date", -1).limit(20))
#         else:
#             posts = list(db.posts.find({"username": username_receive}).sort("date", -1).limit(20))

#         for post in posts:
#             post["_id"] = str(post["_id"])

#             # post heart count(갯수 세기)
#             post["count_heart"] = db.likes.count_documents({"post_id": post["_id"], "type": "heart"})
#             post["heart_by_me"] = bool(
#                 db.likes.find_one({"post_id": post["_id"], "type": "heart", "username": payload['id']}))

#             # post star count
#             post["count_star"] = db.likes.count_documents({"post_id": post["_id"], "type": "star"})
#             post["star_by_me"] = bool(
#                 db.likes.find_one({"post_id": post["_id"], "type": "star", "username": payload['id']}))

#             # post like count
#             post["count_like"] = db.likes.count_documents({"post_id": post["_id"], "type": "like"})
#             post["like_by_me"] = bool(
#                 db.likes.find_one({"post_id": post["_id"], "type": "like", "username": payload['id']}))

#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts":posts})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

#         # Like Update API
#         user_info = db.users.find_one({"username": payload["id"]})
#         post_id_receive = request.form["post_id_give"]
#         type_receive = request.form["type_give"]
#         action_receive = request.form["action_give"]
#         doc = {
#             "post_id": post_id_receive,
#             "username": user_info["username"],
#             "type": type_receive
#         }
#         if action_receive == "like":
#             db.likes.insert_one(doc)
#         else:
#             db.likes.delete_one(doc)
#         count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
#         return jsonify({"result": "success", 'msg': 'updated', "count": count})

#         return jsonify({"result": "success", 'msg': 'updated'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)