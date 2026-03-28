from flask import Blueprint, flash, jsonify, session, redirect, url_for, render_template

from learn_plarm.views.common import mysql_operate

ay = Blueprint("analysis", __name__)

# 学习行为分析API
@ay.route('/api/analysis')
def get_analysis():
    if 'user' not in session:
        flash('用户未登陆','error')
        return jsonify({'error': '用户未登陆'})

    username = session['user']

    # 获取用户id
    sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
    user_id0 = mysql_operate.db.select_db(sql_user_id, (username,))
    print(user_id0)
    user_id = user_id0[0]['id']
    print(user_id)

    # 获取所有课程学习数据
    sql_course = """
        SELECT c.name, uc.total_time
        FROM learn_plarm.Course c
        JOIN learn_plarm.UserCourse uc ON c.id = uc.course_id
        WHERE uc.user_id = %s
        """
    course_data = mysql_operate.db.select_db(sql_course, (user_id,))
    print(course_data)
    total_time = sum(
        c['total_time'] or 0 for c in course_data
    )
    print(total_time)

    # 课程时长分布
    course_distribution = []
    for course in course_data:
        precentage = (course['total_time'] / total_time * 100) if total_time > 0 else 0
        course_distribution.append({
            'name': course['name'],
            'total_time': course['total_time'],
            'percentage': round(precentage, 2)
        })
    print(f'课程时长分布{course_distribution}')

    # 按类别统计
    sql_category = """
        SELECT c.category, SUM(total_time) as total, COUNT(*) as count
        FROM learn_plarm.UserCourse uc
        JOIN learn_plarm.Course c ON uc.course_id = c.id
        WHERE uc.user_id = %s
        GROUP BY c.category
        """
    category_data = mysql_operate.db.select_db(sql_category,(user_id,))

    category_distribution = []
    for cat in category_data:
        category_distribution.append({
            'name': cat['category'] or '其它',
            'value': cat['total'] or 0,
            'count': cat['count']
        })

    # 最近7天学习趋势
    sql_trend = """
        SELECT DATE(created_at) as date, SUM(duration) as total
        FROM learn_plarm.UserBehavior
        WHERE user_id = %s
            #AND behavior_type = 'study'
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date
        """
    trend_data = mysql_operate.db.select_db(sql_trend,(user_id,)) or []
    print(f'trend_data{trend_data}')

    study_trend = []
    for trend in trend_data:
        study_trend.append({
            'date': trend['date'].strftime('%m-%d'),
            'minutes': trend['total'] or 0
        })

    print(total_time, len(course_data), course_distribution, category_distribution,study_trend)

    return jsonify({
        'total_time': total_time,
        'course_count': len(course_data),
        'course_distribution': course_distribution,
        'category_distribution': category_distribution,
        'study_trend': study_trend
    })

# 学习行为分析页面
@ay.route('/analysis')
def analysis():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('analysis.html')