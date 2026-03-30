from flask import render_template, redirect, flash, session, Blueprint, url_for

from learn_plarm.views.common import mysql_operate

dab = Blueprint("dashboard", __name__)

@dab.route('/dashboard')
def dashboard():

    username = session['user']
    print(username)

    # 获取用户信息
    sql = "SELECT id, username, email, avatar FROM learn_plarm.users WHERE username = %s"
    user_data = mysql_operate.db.select_db(sql,(username,))

    if not user_data:
        session.clear()
        flash("用户不存在",'error')
        return redirect('login')

    user = {
        'id': user_data[0].get('id'),
        'username': user_data[0].get('username'),
        'email': user_data[0].get('email') or '',
        'avatar': user_data[0].get('avatar') or 'default_avatar.png'
    }
    user_id = user['id']

    print(user_id)
    print(user.values())

    # 获取用户的课程列表
    sql_course = """
        SELECT c.id, c.name, c.category, c.description, uc.total_time, uc.last_study
        FROM learn_plarm.UserCourse uc
        JOIN learn_plarm.Course c ON uc.course_id = c.id
        WHERE uc.user_id = %s
        ORDER BY uc.last_study DESC
        """
    course_data = mysql_operate.db.select_db(sql_course,(user_id,)) or []
    print(course_data)

    user_course = []
    total_time = 0

    for course in course_data:
        print(course)
        print(type(course)) # dict类型
        user_course.append({
            'id': course['id'],
            'name': course['name'],
            'category': course['category'],
            'description': course['description'],
            'total_time': course['total_time'] or 0,
            'last_study': course['last_study'].strftime('%Y-%m-%d %H:%M') if course['last_study'] else '尚未学习'
        })
        total_time += course['total_time'] or 0

    course_count = len(user_course)
    print(course_count)

    # 获取最近的活动
    sql_activities = """
        SELECT course_id, behavior_type, duration, created_at
        FROM learn_plarm.UserBehavior
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 10
    """
    activities_data = mysql_operate.db.select_db(sql_activities,(user_id,)) or []
    print(f"最近的活动:{type(activities_data)}")  #list类型
    print(activities_data)

    recent_activities = []

    for act in activities_data:
        # 获取课程名称
        print(act) # dict类型
        sql_get_coursename="SELECT name FROM learn_plarm.Course where id = %s"
        course_name_data = mysql_operate.db.select_db(sql_get_coursename,(act['course_id'],))
        print(course_name_data)
        course_name = course_name_data[0]['name'] if course_name_data else '未知课程'

        recent_activities.append({
            'course_name': course_name,
            'behavior': act['behavior_type'],
            'duration': act['duration'] or 0,
            'time': act['created_at'].strftime('%Y-%m-%d %H:%M') if act['created_at'] else ''
        })
        print(recent_activities)

    return render_template('dashboard.html',
                           user = user,
                           user_course = user_course,
                           total_time = total_time,
                           recent_activities = recent_activities)
