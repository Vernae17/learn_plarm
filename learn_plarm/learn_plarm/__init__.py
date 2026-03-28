import os
from flask import Flask
from learn_plarm.views.config.config import config_dict

def create_app():
    # 获取环境变量，默认为 development
    env = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

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
    return app