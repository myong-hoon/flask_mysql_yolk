import re
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


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        sql = "SELECT * FROM users where username = '%s';"
        cursor.execute(sql%(payload["id"]))
        result = cursor.fetchone()
        print(result)

        return render_template('index.html', user_info=result)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    return render_template('login_form01.html')


@app.route('/login/general')
def login2():
    return render_template('login_form02.html')


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

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

    sql = "insert into users(username, password, profile_name, profile_pic_real, profile_pic, profile_info) values(%s, %s, %s, 'profile_pics/profile_placeholder.png','','')"
    cursor.execute(sql,(username_receive,password_hash,username_receive))
    connect.commit()

    return jsonify({'result': 'success'})

# id 중복확인 Server
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
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

        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/"+file_path)
            profile_pic = filename
            profile_pic_real = file_path

        sql = "update users set username = %s, profile_name = %s, profile_info = %s, profile_pic = %s, profile_pic_real = %s where username = %s "
        cursor.execute(sql,(username,name_receive,about_receive,profile_pic,profile_pic_real,username))
        connect.commit()

        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/move', methods=['GET'])
def move():
    return redirect(url_for('/login/general'))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)