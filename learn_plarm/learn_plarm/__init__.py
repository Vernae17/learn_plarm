import os
from flask import Flask, session, redirect, request, flash, url_for
from learn_plarm.views.config.config import config_dict

WHITE_LIST=[
    '/',
    '/login',
    '/regist',
    '/register'
]

def auth():
    for path in WHITE_LIST:
        if request.path == path:
            return

    if request.path.startswith("/static"):
        return

    if 'user' in session:
        return

    # flash("请先登录～", "error")
    print(f"未登录，重定向到 /login")
    return redirect('/login')

def create_app():
    # 获取环境变量，默认为 development
    env = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.secret_key = 'your-secret-key-here' # 用于 flash 消息
    # 初始化生成一个app对象，这个对象就是Flask的当前实例对象，后面的各个方法调用都是这个实例
    # Flask会进行一系列自己的初始化，比如web API路径初始化，web资源加载，日志模块创建等。然后返回这个创建好的对象给你

    # 加载配置
    app.config.from_object(config_dict[env])
    # 打印配置信息（调试用）
    '''print(f"项目根目录: {os.path.abspath(os.path.dirname(__file__))}")
    print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"上传目录是否存在: {os.path.exists(app.config['UPLOAD_FOLDER'])}")'''

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .views import indext, profile, settings, dashboard, mycourse, recommendations, analysis
    app.register_blueprint(indext.id)
    app.register_blueprint(profile.pf)
    app.register_blueprint(settings.st)
    app.register_blueprint(dashboard.dab)
    app.register_blueprint(mycourse.mc)
    app.register_blueprint(recommendations.rc)
    app.register_blueprint(analysis.ay)

    # ai部分
    from .views.ai_assistant import ai_ask,ai_assistant, ai_recommend, assess_progress, generate_plan, generate_quiz, learning_path, summarize_note
    app.register_blueprint(ai_ask.aia)
    app.register_blueprint(ai_assistant.aiat)
    app.register_blueprint(ai_recommend.air)
    app.register_blueprint(assess_progress.aip)
    app.register_blueprint(generate_plan.aigp)
    app.register_blueprint(generate_quiz.aigq)
    app.register_blueprint(learning_path.ail)
    app.register_blueprint(summarize_note.ais)

    app.before_request(auth)
    return app
