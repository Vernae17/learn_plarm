from flask import Blueprint, session, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

aia = Blueprint("ai_ask", __name__)
# ai问答小助手
@aia.route('/api/ai_ask', methods=['POST'])
def ai_ask():

    username = session['user']

    data = request.json
    question = data.get('question')
    course_id = data.get('course_id')

    sql = 'SELECT id FROM learn_plarm.users WHERE username=%s'
    user_id0 = mysql_operate.db.select_db(sql,(username,))
    user_id = user_id0[0]['id']

    # 查找用户所学课程,获取课程上下文
    courses_content = []
    if course_id:
        sql_course = 'SELECT name FROM learn_plarm.Course WHERE id=%s'
        courses = mysql_operate.db.select_db(sql_course,(course_id,))
        if courses:
            courses_content = f"用户正在学的课程：{courses[0]['name']}\n"

    prompt = f"{courses_content}用户问题:{question}"
    answer = call_deepseek(prompt,"你是一个专业的学习助手，耐心解答用户的学习问题")

    # 保存问答记录
    sql_qa = """
            INSERT INTO learn_plarm.qa_records (user_id, course_id, question, answer) 
            VALUES (%s, %s,%s, %s)
            """
    mysql_operate.db.execute_db(sql_qa,(user_id, course_id, question, answer))
    return jsonify({'success':True,'answer':answer})

