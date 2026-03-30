from flask import Blueprint, session, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

ail = Blueprint("learning_path", __name__)


@ail.route("/api/learning_path", methods=['POST'])
def learning_path():
    username = session['user']
    sql_user = 'SELECT id FROM learn_plarm.users WHERE username=%s'
    user_id0 = mysql_operate.db.select_db(sql_user, (username,))
    user_id = user_id0[0]['id']

    data = request.json
    skill = data.get('skill')
    level = data.get('level')

    if not skill:
        return jsonify({'error': '目标技能不能为空'}), 400

    prompt = f"""
    目标技能：{skill}
    当前水平：{level}

    请规划从当前水平到精通的学习路径，包括：
    1. 需要掌握的知识点（按顺序列出）
    2. 推荐的学习资源（书籍、课程、文档）
    3. 实践项目建议
    4. 预计学习时长
    """

    path = call_deepseek(prompt, "你是一个技术学习路径规划专家")

    return jsonify({'success': True, 'path': path})
