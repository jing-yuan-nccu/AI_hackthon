"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    
    # API 配置
    API_PREFIX = '/api'
    
    # AWS 配置
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    AWS_BEDROCK_MODEL = os.environ.get('AWS_BEDROCK_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # 音频文件配置
    AUDIO_DIR = os.environ.get('AUDIO_DIR', '/tmp/audio')
    
    # 确保必要的目录存在
    @staticmethod
    def init_app(app):
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)
        
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') # 生产环境必须设置

# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 当前配置
Config = config[os.environ.get('FLASK_ENV', 'default')] 