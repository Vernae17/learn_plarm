MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "sq040603sx"
MYSQL_DB = "mysql"

# config.py
import os

class Config:
    """基础配置"""
    SECRET_KEY = 'your-secret-key-here'
    # 上传配置
    UPLOAD_FOLDER = os.path.join('/Users/nicole/PycharmProjects/learn_plarm/learn_plarm', 'static', 'uploads', 'avatars')
    print(UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境使用绝对路径
    UPLOAD_FOLDER = os.path.join('/Users/nicole/PycharmProjects/learn_plarm/learn_plarm', 'static', 'uploads', 'avatars')
    # print(UPLOAD_FOLDER)


# 配置字典
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}