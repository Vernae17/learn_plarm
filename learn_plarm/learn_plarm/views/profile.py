import jsonify
from flask import Blueprint, session, flash, redirect, render_template, url_for

from learn_plarm.views.common import mysql_operate

pf = Blueprint("profile", __name__)

# 个人资料页面
@pf.route('/profile')
def profile():
    if 'user' not in session:
        flash('用户未登陆', 'error')
        return jsonify({'error': '用户不存在'})

    username = session['user']

    sql_userdata = """
        SELECT id, username, email, avatar, created_at FROM learn_plarm.users WHERE username = %s
        """
    user_data = mysql_operate.db.select_db(sql_userdata,(username,))
    print(f'userdata:{user_data}')

    if not user_data:
        session.clear()
        return redirect(url_for('login'))

    user = {
        'username': user_data[0]['username'],
        'email': user_data[0]['email'],
        'avatar': user_data[0]['avatar'],
        'created_at': user_data[0]['created_at']
    }
    return render_template("profile.html",user = user)
