from flask import Blueprint, session, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

aigq = Blueprint("generate_quiz", __name__)

# 生成试题
@aigq.route("/api/generate_quiz", methods=['POST'])
def generate_quiz():
    if 'user' not in session:
        flash({'error': '用户未登陆'})
        return jsonify({'error': '请重新登录'})

    username = session['user']
    sql_user = 'SELECT id FROM learn_plarm.users WHERE username=%s'
    user_id0 = mysql_operate.db.select_db(sql_user, (username,))
    user_id = user_id0[0]['id']

    data = request.json
    course_name = data.get('course')
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'medium')
    question_count = data.get('count', 5)

    if not topic:
        return jsonify({'error': '请输入知识点'})

    try:
        prompt = f"""
                课程：{course_name or '通用'}
                知识点：{topic}
                难度：{difficulty}
                题目数量：{question_count}

                请生成一套练习题，包含选择题、判断题和简答题，并标注正确答案和答案解析。
                """

        quiz = call_deepseek(prompt, '你是一个专业的试题设计专家')

        # 保存试题信息
        sql = 'INSERT INTO learn_plarm.quizzes (user_id, course_name, topic, difficulty, questions) VALUES (%s, %s, %s, %s, %s)'
        mysql_operate.db.execute_db(sql, (user_id, course_name, topic, difficulty, quiz))

        return jsonify({'success': True, 'quiz': quiz})

    except Exception as e:
        return jsonify({'error': str(e)})
