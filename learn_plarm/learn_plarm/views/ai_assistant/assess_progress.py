from flask import Blueprint, session, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

aip = Blueprint("assess_progress", __name__)

# 学习进度评估
@aip.route("/api/assess_progress")
def assess_progress():
    username = session['user']

    try:
        sql_user = 'SELECT id FROM learn_plarm.users WHERE username=%s'
        user_id0 = mysql_operate.db.select_db(sql_user, (username,))
        user_id = user_id0[0]['id']

        # 查询用户所学课程有哪些,花了多少时间
        sql_course = """
            SELECT c.name,c.category,uc.total_time,uc.last_study
            FROM learn_plarm.Course c
            JOIN learn_plarm.UserCourse uc ON c.id = uc.course_id
            WHERE user_id=%s
            """
        course_date = mysql_operate.db.select_db(sql_course,(user_id,))
        # print(f"course_date:{course_date}")

        # 查询用户学习行为
        sql_behavior ="""
            SELECT behavior_type,duration,created_at
            FROM learn_plarm.UserBehavior
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 50
            """
        behavior_data = mysql_operate.db.select_db(sql_behavior,(user_id,))

        # 进度评估：需要的数据：学习课程，学习时长，总时长，进度比=学习时长/总时长，原计划多少天，预计还需要多少天==ai做算法给评估
        prompt = f"""
            用户学习数据：
            用户课程信息：{course_date}
            用户学习行为：{behavior_data}
            请评估用户的学习情况，包括：
            1.学习进度分析，最好能用图表的方式展示出来
            2.学习效率分析
            3.知识点掌握情况
            4.存在的问题和不足
            5.改进建议
            """
        assessment = call_deepseek(prompt,'你是一个学习分析专家')

        sql = 'INSERT INTO learn_plarm.learning_assessments (user_id,assessment_content) VALUES (%s,%s)'
        mysql_operate.db.execute_db(sql,(user_id,assessment))

        return jsonify({'success':True,'assessment':assessment})

    except Exception as e:
        print(f"评估错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 加载历史评估
@aip.route("/api/get_assessments")
def get_assessments():

    username = session['user']
    sql_user = 'SELECT id FROM learn_plarm.users WHERE username=%s'
    user_id0 = mysql_operate.db.select_db(sql_user, (username,))
    user_id = user_id0[0]['id']

    # 获取历史评估
    sql = 'SELECT assessment_content,created_at FROM learn_plarm.learning_assessments WHERE user_id=%s'
    assessments = mysql_operate.db.select_db(sql,(user_id,))

    # 打印查询结果数量
    # print(f"查询到 {len(assessments) if assessments else 0} 条评估记录")

    # 打印每条记录的ID，确认是否是最新数据
    if assessments:
        for ass in assessments:
            print(f"评估ID: {ass.get('id')}, 时间: {ass.get('created_at')}")

    return jsonify({'success':True,'assessments':assessments,'message':'评估完成'})