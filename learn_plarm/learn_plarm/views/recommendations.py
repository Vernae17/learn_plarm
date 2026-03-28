from flask import Blueprint, flash, session, jsonify, redirect, url_for, render_template

from learn_plarm.views.common import mysql_operate

rc = Blueprint("recommendations", __name__)

# 个性化API推荐
@rc.route('/api/recommendations')
def get_recommendations():
    if 'user' not in session:
        flash('用户未登陆','error')
        return jsonify({'error': '用户未登陆'})

    username = session['user']

    # 获取用户id
    sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
    user_id0 = mysql_operate.db.select_db(sql_user_id, (username,))
    user_id = user_id0[0]['id']
    # 获取用户的所有课程
    sql_course = """
        SELECT uc.course_id, c.name, uc.total_time
        FROM learn_plarm.UserCourse uc
        JOIN learn_plarm.Course c ON uc.course_id = c.id
        WHERE user_id = %s
        """
    course_data = mysql_operate.db.select_db(sql_course,(user_id,)) or []

    recommendations = []

    if len(course_data) < 2:
        # 课程太少，推荐添加新课程
        sql_other = """
            SELECT id, name, description
            FROM learn_plarm.Course
            WHERE id NOT IN(
                SELECT uc.course_id 
                FROM learn_plarm.UserCourse uc
                WHERE user_id = %s
            )
            LIMIT 3
            """
        other_course = mysql_operate.db.select_db(sql_other, (user_id,)) or []

        for course in other_course:
            recommendations.append({
                'type': 'new_course',
                'title': f'📚 探索新领域',
                'description': f'试试学习"{course["description"]}"，拓展知识面',
                'course_id': course['id'],
                'priority': 'medium'
            })
    else:
        # 计算平均学习时长
        total_time = sum(c['total_time'] for c in course_data)
        avg_total = total_time / len(course_data)

        #找出学习时间最短的课程
        course_data.sort(key=lambda x: x['total_time'] or 0)
        shortest = course_data[0]
        if (shortest['total_time'] or 0) < avg_total * 0.5:
            recommendations.append({
                'type': 'focus',
                'title': f'🎯 需要多花点时间',
                'description': f'你在"{shortest["name"]}"上的学习时间较少，建议增加学习时长',
                'course_id': shortest['course_id'],
                'priority': 'high'
            })

        #学习均衡表扬
        balenced = [c for c in course_data if abs((c['total_time'] or 0) - avg_total) <avg_total * 0.2]
        if len(balenced) >= 2:
            recommendations.append({
                'type': 'praise',
                'title': '🌟 学习均衡达人',
                'description': '你的学习时间分配很均衡，继续保持！',
                'priority': 'medium'
            })

        print(recommendations)

    return jsonify(recommendations)

# 个性化推荐页面
@rc.route('/recommendations')
def recommendations():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('recommendations.html')