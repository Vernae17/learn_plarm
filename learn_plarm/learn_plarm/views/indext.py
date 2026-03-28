import  bcrypt
from flask import Blueprint, session, url_for, flash, render_template, redirect ,request
from learn_plarm.views.common import mysql_operate

id = Blueprint("index", __name__)


def get_user_avatar(username):
    """获取用户头像"""
    sql = "SELECT avatar FROM learn_plarm.users WHERE username = %s"
    data = mysql_operate.db.select_db(sql, (username,))
    print(data)
    print(type(data))  # list类型
    if data and len(data) > 0:
        avatar = data[0].get('avatar')
        if avatar:
            return avatar
    return 'default_avatar.png'

@id.route("/") # 登陆
def login():
    return render_template("index.html")

@id.route("/logout") # 退出
def logout():
    flash('已退出，请重新登陆～','info')
    return redirect(url_for('login'))

@id.route("/regist") # 注册
def regist():
    return render_template("register.html")

# 登陆
@id.route("/login", methods=['POST'])
def getLoginRequest():
    # 使用 request.form 获取POST数据
    username = str(request.form.get("username"))
    password = str(request.form.get("password"))

    print(f"1. 接收到的用户名：'{username}'，密码：'{password}'")

    if not username or not password:
        flash('用户名和密码不能为空','error')
        return render_template("index.html")

    #使用参数化查询防止SQL注入
    sql = "select * from learn_plarm.users where username = %s"
    data = mysql_operate.db.select_db(sql,(username,))

    if data:
        stored_password = data[0]['password']  # 获取数据库中存储的密码哈希

        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            # 登录成功，设置session
            session['user'] = username
            session['logged_in'] = True

            # 获取该用户头像
            avatar = get_user_avatar(username)
            session['avatar'] = avatar

            flash('登陆成功','success')
            return redirect("/dashboard")
        else:
            flash('用户名或密码错误，请重新登录！','error')
            return render_template("index.html")
    else:
        flash('用户名或密码错误，请重新登录！', 'error')
        return render_template("index.html")

# 注册
@id.route("/register",methods=['POST'])
def getRegisterRequest():
    if request.method == 'GET':
        return render_template("register.html")

    username = str(request.form.get('username'))
    password = str(request.form.get('password'))
    email = str(request.form.get('email', ''))

    sql = "select * from learn_plarm.users where username = %s"
    data = mysql_operate.db.select_db(sql,(username,))

    if data:
        flash('账号已注册，请直接登陆～','error')
        return render_template("index.html")
    else:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8') # 密码加密
        print(f"哈希长度: {len(hashed_password)}")  # 应该小于 128
        sql1 = "insert into learn_plarm.users (username,password,email,avatar) values (%s,%s,%s,%s);"
        mysql_operate.db.execute_db(sql1,(username,hashed_password,email,'default_avatar.png'))
        flash('注册成功，请返回登陆～','sucess')
        return render_template("index.html")