from flask import Blueprint , flash, jsonify, session, request, render_template, redirect, url_for, current_app
import os, datetime, bcrypt
from werkzeug.utils import secure_filename
from learn_plarm.views.common import mysql_operate
from flask import current_app

st = Blueprint("settings", __name__)

# 上传配置
''' UPLOAD_FOLDER = 'learn_plarm/static/uploads/avatars' '''
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def update_user_avatar(username, avatar_filename):
    '''更新用户头像'''
    sql = "UPDATE learn_plarm.users SET avatar = %s WHERE username = %s"
    mysql_operate.db.execute_db(sql,(avatar_filename,username))

def update_user_email(username,email):
    '''更新用户邮箱'''
    sql = "UPDATE learn_plarm.users SET email = %s WHERE username = %s"
    mysql_operate.db.execute_db(sql, (email,username))

def update_user_password(username,new_password):
    '''更新用户密码（bcrypt 加密）'''
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
    sql = "UPDATE learn_plarm.users SET password = %s WHERE username = %s"
    mysql_operate.db.execute_db(sql, (hashed_password,username))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 设置页面
@st.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        flash('用户未登陆', 'error')
        return jsonify({'error': '用户不存在'})

    username = session['user']

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            print(old_password)

            if not old_password or not new_password:
                flash({'请填写所有密码字段': 'error'})

            # 验证原密码
            sql_oldpw = "SELECT password FROM learn_plarm.users WHERE username = %s"
            old_pw_data = mysql_operate.db.select_db(sql_oldpw,(username,))
            print(old_pw_data)

            if old_pw_data and old_pw_data[0]['password']:
                stored_password = old_pw_data[0]['password']
                # 使用 bcrypt 验证
                if bcrypt.checkpw(old_password.encode('utf-8'), stored_password.encode('utf-8')):
                    # 更新密码
                    update_user_password(username,new_password)
                    flash('密码修改成功', 'success')
                else:
                    flash('密码修改失败', 'error')
            else:
                flash('密码修改失败', 'error')

        elif action == 'avatar':
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and allowed_file(file.filename):
                    # 生成唯一文件名
                    ext = file.filename.rsplit('.',1)[1].lower()
                    timestamp = int(datetime.datetime.now().timestamp())
                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/avatars')
                    print(upload_folder)
                    filename = secure_filename(f'avatar_{username}_{timestamp}.{ext}')
                    filepath = os.path.join(upload_folder, filename)
                    print(filepath)
                    file.save(filepath)

                    # 更新数据库
                    update_user_avatar(username,filename)
                    session['avatar'] = filename
                    flash({'头像更新成功': 'success'})
                else:
                    flash({'文件类型不允许，请上传 png、jpg、jpeg、gif 格式的图片': 'error'})
            else:
                flash({'请选择要上传的文件': 'error'})

        elif action == 'info':
            email = request.form.get('email')
            if email:
                update_user_email(username,email)
                flash({'信息更新成功': 'success'})
            else:
                flash({'邮箱不能为空': 'error'})

        return redirect(url_for('settings.settings'))

    # GET请求
    sql = "SELECT username, email, avatar, created_at FROM learn_plarm.users WHERE username = %s"
    user_data = mysql_operate.db.select_db(sql, (username,))

    if not user_data:
        session.clear()
        flash({'用户不存在': 'error'})
        return redirect(url_for('login'))

    user = {
        'username': user_data[0]['username'],
        'email': user_data[0]['email'],
        'avatar': user_data[0]['avatar'] or 'default_avatar.png',
        'created_at': user_data[0]['created_at'] or 0
    }

    return render_template('settings.html', user = user)