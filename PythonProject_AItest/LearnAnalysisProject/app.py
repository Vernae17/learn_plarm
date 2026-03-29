# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from models import db, User, Course, UserCourse, UserBehavior
from datetime import datetime, timedelta
import os
import hashlib
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sq040603sx'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:sq040603sx@localhost/learn_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 上传配置
UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db.init_app(app)

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_user():
    """在模板中注入当前用户"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    '''user = User.query.get(session['user_id'])

    # 获取用户的课程列表
    user_courses = UserCourse.query.filter_by(user_id=user.id).all()

    # 计算学习统计
    total_time = sum(uc.total_time for uc in user_courses)
    course_count = len(user_courses)

    # 获取最近学习活动
    recent_activities = UserBehavior.query.filter_by(
        user_id=user.id
    ).order_by(UserBehavior.created_at.desc()).limit(10).all(),
                           user=user,
                           user_courses=user_courses,
                           total_time=total_time,
                           course_count=course_count,
                           recent_activities=recent_activities'''

    return render_template('dashboard.html')


@app.route('/api/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    user_id = session['user_id']

    if request.method == 'GET':
        # 获取用户的所有课程
        user_courses = UserCourse.query.filter_by(user_id=user_id).all()
        courses_data = []
        for uc in user_courses:
            course = Course.query.get(uc.course_id)
            courses_data.append({
                'id': uc.id,
                'course_id': course.id,
                'name': course.name,
                'description': course.description,
                'category': course.category,
                'total_time': uc.total_time,
                'last_study': uc.last_study.strftime('%Y-%m-%d %H:%M') if uc.last_study else None
            })
        return jsonify(courses_data)

    elif request.method == 'POST':
        # 添加课程
        data = request.json
        course_name = data.get('name')
        course_category = data.get('category', '其他')

        # 查找或创建课程
        course = Course.query.filter_by(name=course_name).first()
        if not course:
            course = Course(name=course_name, category=course_category)
            db.session.add(course)
            db.session.commit()

        # 检查是否已添加
        existing = UserCourse.query.filter_by(
            user_id=user_id,
            course_id=course.id
        ).first()

        if existing:
            return jsonify({'error': '课程已存在'}), 400

        # 添加到用户课程
        user_course = UserCourse(
            user_id=user_id,
            course_id=course.id
        )
        db.session.add(user_course)

        # 记录行为
        behavior = UserBehavior(
            user_id=user_id,
            course_id=course.id,
            behavior_type='add'
        )
        db.session.add(behavior)
        db.session.commit()

        return jsonify({'success': True, 'course_id': course.id})


@app.route('/api/courses/<int:course_id>', methods=['DELETE', 'PUT'])
def delete_course(course_id):
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    user_id = session['user_id']
    user_course = UserCourse.query.filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()

    if not user_course:
        return jsonify({'error': '课程不存在'}), 404

    if request.method == 'DELETE':
        # 删除课程
        db.session.delete(user_course)

        # 记录行为
        behavior = UserBehavior(
            user_id=user_id,
            course_id=course_id,
            behavior_type='remove'
        )
        db.session.add(behavior)
        db.session.commit()

        return jsonify({'success': True})

    elif request.method == 'PUT':
        # 更新学习时长
        data = request.json
        duration = data.get('duration', 0)

        user_course.total_time += duration
        user_course.last_study = datetime.now()

        # 记录学习行为
        behavior = UserBehavior(
            user_id=user_id,
            course_id=course_id,
            behavior_type='study',
            duration=duration
        )
        db.session.add(behavior)
        db.session.commit()

        return jsonify({'success': True, 'total_time': user_course.total_time})


@app.route('/api/study/session', methods=['POST'])
def record_study_session():
    """记录学习会话"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    data = request.json
    course_id = data.get('course_id')
    duration = data.get('duration', 0)

    user_course = UserCourse.query.filter_by(
        user_id=session['user_id'],
        course_id=course_id
    ).first()

    if user_course:
        user_course.total_time += duration
        user_course.last_study = datetime.now()

        behavior = UserBehavior(
            user_id=session['user_id'],
            course_id=course_id,
            behavior_type='study',
            duration=duration
        )
        db.session.add(behavior)
        db.session.commit()

        return jsonify({'success': True})

    return jsonify({'error': '课程不存在'}), 404


@app.route('/api/analysis')
def get_analysis():
    """获取学习分析数据"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    user_id = session['user_id']

    # 获取所有课程学习数据
    user_courses = UserCourse.query.filter_by(user_id=user_id).all()

    # 计算总学习时间
    total_time = sum(uc.total_time for uc in user_courses)

    # 课程时长分布（用于饼图）
    course_distribution = []
    for uc in user_courses:
        course = Course.query.get(uc.course_id)
        percentage = (uc.total_time / total_time * 100) if total_time > 0 else 0
        course_distribution.append({
            'name': course.name,
            'value': uc.total_time,
            'percentage': round(percentage, 2)
        })

    # 按类别统计
    category_stats = {}
    for uc in user_courses:
        course = Course.query.get(uc.course_id)
        category = course.category
        if category not in category_stats:
            category_stats[category] = {
                'total_time': 0,
                'course_count': 0
            }
        category_stats[category]['total_time'] += uc.total_time
        category_stats[category]['course_count'] += 1

    category_data = [
        {
            'name': cat,
            'value': stats['total_time'],
            'count': stats['course_count']
        }
        for cat, stats in category_stats.items()
    ]

    # 最近7天学习趋势
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    daily_study = db.session.query(
        db.func.date(UserBehavior.created_at).label('date'),
        db.func.sum(UserBehavior.duration).label('total')
    ).filter(
        UserBehavior.user_id == user_id,
        UserBehavior.behavior_type == 'study',
        UserBehavior.created_at >= start_date
    ).group_by('date').all()

    study_trend = [
        {
            'date': d.date.strftime('%m-%d'),
            'minutes': d.total or 0
        }
        for d in daily_study
    ]

    return jsonify({
        'total_time': total_time,
        'course_count': len(user_courses),
        'course_distribution': course_distribution,
        'category_distribution': category_data,
        'study_trend': study_trend
    })


@app.route('/api/recommendations')
def get_recommendations():
    """获取个性化推荐"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    user_id = session['user_id']

    # 获取用户的所有课程
    user_courses = UserCourse.query.filter_by(user_id=user_id).all()

    if len(user_courses) < 2:
        # 课程太少，推荐添加新课程
        all_courses = Course.query.limit(5).all()
        recommendations = []
        for course in all_courses:
            if not any(uc.course_id == course.id for uc in user_courses):
                recommendations.append({
                    'type': 'new_course',
                    'title': f'推荐学习：{course.name}',
                    'description': course.description,
                    'course_id': course.id,
                    'priority': 'medium'
                })
        return jsonify(recommendations[:3])

    # 计算各课程的学习时长
    course_times = [(uc.course_id, uc.total_time) for uc in user_courses]
    course_times.sort(key=lambda x: x[1])

    # 找出学习时间最短和最长的课程
    shortest = course_times[0]
    longest = course_times[-1]

    avg_time = sum(t for _, t in course_times) / len(course_times)

    recommendations = []

    # 1. 时间差距较大的课程
    if longest[1] > avg_time * 1.5:
        course_long = Course.query.get(longest[0])
        recommendations.append({
            'type': 'balance',
            'title': '⏰ 学习时间分配提醒',
            'description': f'你在"{course_long.name}"上花费了最多时间，建议适当平衡各科学习时间',
            'course_id': longest[0],
            'priority': 'high'
        })

    # 2. 时间较短的课程
    for course_id, time in course_times[:2]:
        if time < avg_time * 0.5:
            course_short = Course.query.get(course_id)
            recommendations.append({
                'type': 'focus',
                'title': f'🎯 需要多花点时间',
                'description': f'你在"{course_short.name}"上的学习时间较少，建议增加学习时长',
                'course_id': course_id,
                'priority': 'high'
            })

    # 3. 学习均衡的表扬
    if len([t for _, t in course_times if abs(t - avg_time) < avg_time * 0.2]) >= 2:
        recommendations.append({
            'type': 'praise',
            'title': '🌟 学习均衡达人',
            'description': '你的学习时间分配很均衡，继续保持！',
            'priority': 'medium'
        })

    # 4. 推荐新课程
    if len(user_courses) < 5:
        other_courses = Course.query.filter(
            ~Course.id.in_([uc.course_id for uc in user_courses])
        ).limit(2).all()
        for course in other_courses:
            recommendations.append({
                'type': 'explore',
                'title': f'📚 探索新领域',
                'description': f'试试学习"{course.name}"，拓展知识面',
                'course_id': course.id,
                'priority': 'low'
            })

    return jsonify(recommendations[:5])


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'password':
            # 修改密码
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')

            if user.check_password(old_password):
                user.set_password(new_password)
                db.session.commit()
                flash('密码修改成功', 'success')
            else:
                flash('原密码错误', 'error')

        elif action == 'avatar':
            # 修改头像
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"user_{user.id}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)

                    # 更新数据库
                    user.avatar = filename
                    db.session.commit()
                    flash('头像更新成功', 'success')

        elif action == 'info':
            # 更新个人信息
            email = request.form.get('email')
            if email:
                user.email = email
                db.session.commit()
                flash('信息更新成功', 'success')

        return redirect(url_for('settings'))

    return render_template('settings.html', user=user)


@app.route('/analysis')
def analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('analysis.html', user=user)


# 初始化示例数据
@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    db.create_all()

    # 添加示例课程
    courses = [
        {'name': 'Python基础', 'category': '编程', 'description': 'Python编程语言基础教程'},
        {'name': '数据结构', 'category': '计算机科学', 'description': '常见数据结构和算法'},
        {'name': 'Web开发', 'category': '编程', 'description': 'Flask和Django框架'},
        {'name': '机器学习', 'category': '人工智能', 'description': '机器学习基础'},
        {'name': '数据库设计', 'category': '计算机科学', 'description': 'MySQL和MongoDB'},
        {'name': '英语口语', 'category': '语言', 'description': '日常英语对话'},
        {'name': '日语入门', 'category': '语言', 'description': '五十音图和基础语法'},
    ]

    for course_data in courses:
        if not Course.query.filter_by(name=course_data['name']).first():
            course = Course(**course_data)
            db.session.add(course)

    db.session.commit()
    print('数据库初始化完成！')


if __name__ == '__main__':
    app.run(debug=True)