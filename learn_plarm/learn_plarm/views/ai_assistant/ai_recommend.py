from flask import Blueprint, session,  flash, jsonify

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

air = Blueprint("ai_recommend", __name__)

# 智能课程推荐
@air.route('/api/ai_recommend', methods=['POST'])
def ai_recommend():
    """基于大模型的智能课程推荐"""
    username = session['user']

    # 获取用户学习数据
    sql_user = 'SELECT id FROM learn_plarm.users WHERE username = %s'
    user_id0 = mysql_operate.db.select_db(sql_user, (username,))
    user_id = user_id0[0]['id']

    sql_courses = """
        SELECT c.name, c.category, uc.total_time
        FROM learn_plarm.Course c
        JOIN learn_plarm.UserCourse uc
        ON c.id = uc.course_id
        WHERE uc.user_id = %s
        """
    courses = mysql_operate.db.select_db(sql_courses, (user_id,))
    print(f"courses:{courses}")

    # 构建提示词
    prompt = f"""
        用户的学习记录：
        {courses}

        请根据以上学习记录，推荐3个适合用户下一步学习的课程方向。
        要求：
        1. 分析用户的学习兴趣和偏好
        2. 考虑学习的连贯性和进阶性
        3. 给出具体的推荐理由
        返回格式：JSON格式，包含course_name, reason, difficulty
        """

    result =  call_deepseek(prompt, "你是一个专业的学习顾问，擅长分析学习数据并提供个性化建议。")
    print(f"/api/ai_recommend result:{result}")
    print(type(result))

    return jsonify({'success': True, 'recommendations':result})