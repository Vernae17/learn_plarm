from flask import Blueprint, session, redirect, render_template, url_for, jsonify, flash, request

from learn_plarm.views.common import mysql_operate

mc = Blueprint("mycourse", __name__)

# 我的课程页面
@mc.route('/mycourse')
def mycourse():
    username = session['user']
    # print(username)

    # 获取用户信息
    sql = "SELECT id, username, email, avatar FROM learn_plarm.users WHERE username = %s"
    user_data = mysql_operate.db.select_db(sql, (username,))

    # 获取该用户的id
    sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
    user_id0 = mysql_operate.db.select_db(sql_user_id, (username,))
    user_id = user_id0[0]['id']

    # 获取用户的课程列表
    sql_course = """
            SELECT c.id, c.name, c.category, c.description, uc.total_time, uc.last_study
            FROM learn_plarm.UserCourse uc
            JOIN learn_plarm.Course c ON uc.course_id = c.id
            WHERE uc.user_id = %s
            ORDER BY uc.last_study DESC
            """
    course_data = mysql_operate.db.select_db(sql_course, (user_id,)) or []
    # print(course_data)

    user_course = []
    total_time = 0

    for course in course_data:
        print(course)
        print(type(course))  # dict类型
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
    # print(course_count)

    # 获取最近的活动
    sql_activities = """
            SELECT course_id, behavior_type, duration, created_at
            FROM learn_plarm.UserBehavior
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """
    activities_data = mysql_operate.db.select_db(sql_activities, (user_id,)) or []
    print(f"最近的活动:{type(activities_data)}")  # list类型
    print(activities_data)

    recent_activities = []

    for act in activities_data:
        # 获取课程名称
        print(act)  # dict类型
        sql_get_coursename = "SELECT name FROM learn_plarm.Course where id = %s"
        course_name_data = mysql_operate.db.select_db(sql_get_coursename, (act['course_id'],))
        print(course_name_data)
        course_name = course_name_data[0]['name'] if course_name_data else '未知课程'

        recent_activities.append({
            'course_name': course_name,
            'behavior': act['behavior_type'],
            'duration': act['duration'] or 0,
            'time': act['created_at'].strftime('%Y-%m-%d %H:%M') if act['created_at'] else ''
        })
        print(recent_activities)

    return render_template('mycourse.html',
                           user_course=user_course,
                           total_time=total_time,
                           recent_activities=recent_activities
                           )

# 获取单个课程信息
@mc.route('/get_course/<int:course_id>', methods=['GET'])
def get_course(course_id):
    username = session['user']

    try:
        # 获取用户id
        sql_user_id = 'SELECT id FROM learn_plarm.users WHERE username = %s'
        user_id0 = mysql_operate.db.select_db(sql_user_id,(username,))
        user_id = user_id0[0]['id']

        # 获取课程信息
        sql_course = """
                 SELECT c.id, c.name, c.category, c.description, uc.last_study
                 FROM learn_plarm.Course c
                 JOIN learn_plarm.UserCourse uc ON c.id = uc.course_id
                 WHERE c.id = %s AND user_id = %s
                 """
        course_data = mysql_operate.db.select_db(sql_course, (course_id, user_id)) or []

        if not course_data:
            return jsonify({'error','课程不存在'})
            # 处理数据格式
        if isinstance(course_data[0], dict):
            course = {
                'id': course_data[0].get('id'),
                'name': course_data[0].get('name'),
                'category': course_data[0].get('category'),
                'description': course_data[0].get('description', ''),
                'last_study': course_data[0].get('last_study')
            }
        else:
            course = {
                'id': course_data[0][0],
                'name': course_data[0][1],
                'category': course_data[0][2],
                'description': course_data[0][3] if len(course_data[0]) > 3 else '',
                'last_study': course_data[0][4] if len(course_data[0]) > 4 else None
            }
        print(f'get_course:{course_data}')
        return jsonify(course)


    except Exception as e:
        print(f"获取课程错误: {e}")
        return jsonify({'error': str(e)}), 500

# 添加课程
@mc.route('/add_course', methods=['POST'])
def add_course():

    data = request.json
    course_name = data.get('name')
    category = data.get('category','其他')
    description = data.get('description','')

    username = session['user']

    # 获取该用户的id
    sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
    user_id0 = mysql_operate.db.select_db(sql_user_id,(username,))
    user_id = user_id0[0]['id']
    # 检查课程是否已存在
    sql_check = "SELECT id FROM learn_plarm.Course WHERE name = %s"
    course_data = mysql_operate.db.select_db(sql_check,(course_name,))

    # print(type(course_data))
    if course_data and len(course_data) > 0:
        course_id = course_data[0]['id']
    else:
        # 添加新课程
        sql_add_course = "INSERT INTO learn_plarm.Course(name, category, description) VALUES (%s, %s, %s)"
        mysql_operate.db.execute_db(sql_add_course,(course_name, category, description))

        # 获取新插入的课程id
        sql_last_id = 'SELECT LAST_INSERT_ID() FROM learn_plarm.Course'
        course_id0 = mysql_operate.db.select_db(sql_last_id)
        print(f'course_id0:{course_id0}')
        course_id = course_id0[0]['id']

    # print(f'course_id{course_id}')
    #检查用户是否已经添加该课程
    sql_check_user = "SELECT id FROM learn_plarm.UserCourse WHERE user_id = %s AND course_id = %s"
    user_course = mysql_operate.db.select_db(sql_check_user,(user_id,course_id))

    if user_course and len(user_course) > 0:
        return jsonify({'error':'已添加该课程'}), 400

    # 添加到用户课程
    sql_usercourse = "INSERT INTO learn_plarm.UserCourse(user_id, course_id) VALUES (%s, %s)"
    mysql_operate.db.execute_db(sql_usercourse,(user_id,course_id))

    # 记录行为-添加用户行为
    sql_behavior = """
        INSERT INTO learn_plarm.UserBehavior(user_id, course_id, behavior_type) VALUES (%s, %s, 'add')
        """
    mysql_operate.db.execute_db(sql_behavior,(user_id,course_id))

    # print(f'添加课程:{course_data}')

    return jsonify({'success': True, 'course_id': course_id})

# 编辑课程
@mc.route('/update_course/<int:course_id>', methods = ['PUT'])
def update_course(course_id):

    data = request.json
    course_name = data.get('name')
    category = data.get('category', '其他')
    description = data.get('description', '')
    last_study = data.get('last_study')

    username = session['user']

    # 获取用户id
    sql_userid = 'SELECT id FROM learn_plarm.users WHERE username = %s'
    user_id0 = mysql_operate.db.select_db(sql_userid, (username,))
    user_id = user_id0[0]['id']

    # print(f"更新课程: course_id={course_id}, user_id={user_id}")

    # 查询更新前的数据
    sql_before = 'SELECT * FROM learn_plarm.UserCourse WHERE course_id = %s AND user_id = %s'
    before_data = mysql_operate.db.select_db(sql_before,(course_id, user_id))
    # print(f'查询更新前的数据{before_data}')

    # 修改课程名称/课程类别
    sql_changeCourse = """
        UPDATE learn_plarm.Course
        SET name = %s, description = %s, category = %s
        WHERE id = %s
        """
    mysql_operate.db.execute_db(sql_changeCourse, (course_name, description, category, course_id))

    #修改上次学习时间
    # 如果有传入时间，使用传入时间；否则使用当前时间
    if last_study:
        sql = "UPDATE learn_plarm.UserCourse SET last_study = %s WHERE course_id = %s AND user_id = %s"
        mysql_operate.db.execute_db(sql, (last_study, course_id, user_id))
    else:
        sql = "UPDATE learn_plarm.UserCourse SET last_study = NOW() WHERE course_id = %s AND user_id = %s"
        mysql_operate.db.execute_db(sql, (course_id, user_id))

    # 查询更新后的数据
    sql_after = 'SELECT * FROM learn_plarm.UserCourse WHERE course_id = %s AND user_id = %s'
    after_data = mysql_operate.db.select_db(sql_after, (course_id, user_id))
    # print(f'查询更新后的数据{after_data}')

    return jsonify({'success': True})

# 记录学习时长
@mc.route('/record_study', methods = ['POST'])
def record_study():

    data = request.json
    course_id = data.get('course_id')
    duration = data.get('duration', 0)

    username = session['user']

    sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
    user_id_data = mysql_operate.db.select_db(sql_user_id, (username,))
    if not user_id_data:
        return jsonify({'error': '用户不存在'}), 404

    user_id = user_id_data[0]['id']

    # 更新学习时长
    sql_update = """
        UPDATE learn_plarm.UserCourse
        SET total_time = total_time + %s, last_study = NOW()
        WHERE user_id = %s AND course_id = %s
        """
    mysql_operate.db.execute_db(sql_update,(duration,user_id,course_id))

    # 记录行为
    sql_behavior = """
        INSERT INTO learn_plarm.UserBehavior(user_id, course_id, behavior_type, duration) 
        VALUES (%s, %s, 'study', %s)
        """
    mysql_operate.db.execute_db(sql_behavior, (user_id, course_id, duration))

    return jsonify({'succes': True})

# 删除课程
@mc.route('/delete_course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):

    username = session['user']

    try:
        # 获取该用户的id
        sql_user_id = "SELECT id FROM learn_plarm.users WHERE username = %s"
        user_id0 = mysql_operate.db.select_db(sql_user_id, (username,))
        user_id = user_id0[0]['id']

        if not user_id0:
            return jsonify({'error': '用户不存在'}), 404

        # 检查课程是否存在且属于该用户
        check_sql = "SELECT id FROM learn_plarm.UserCourse WHERE user_id = %s AND course_id = %s"
        course_exists = mysql_operate.db.select_db(check_sql, (user_id, course_id))

        if not course_exists:
            print(f"课程不存在或不属于当前用户: course_id={course_id}, user_id={user_id}")
            return jsonify({'error': '课程不存在'}), 404

        # 记录删除行为
        sql_behavior = """
                INSERT INTO learn_plarm.UserBehavior (user_id, course_id, behavior_type) 
                VALUES (%s, %s, 'remove')
            """
        mysql_operate.db.execute_db(sql_behavior, (user_id, course_id))

        # 删除课程
        sql_delete = "DELETE FROM learn_plarm.UserCourse WHERE user_id = %s AND course_id = %s"
        mysql_operate.db.execute_db(sql_delete, (user_id, course_id))

        return jsonify({'success': True})

    except Exception as e:
        print(f"删除课程错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
