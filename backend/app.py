"""
AI_hackthon Flask应用入口点
"""
import os
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_app():
    """
    创建并配置Flask应用
    """
    # 初始化Flask应用
    app = Flask(__name__)
    
    # 配置跨域资源共享
    CORS(app)
    
    
    # 配置应用
    app.config.from_object('config.Config')
    app.config['JSON_AS_ASCII'] = False
    # **加这一行**：创建好 AUDIO_DIR
    from config import Config
    Config.init_app(app)

    # 注册API蓝图
    from api.llm import llm_bp
    from api.speech import speech_bp
    from api.session import session_bp
    
    app.register_blueprint(llm_bp)
    app.register_blueprint(speech_bp)
    app.register_blueprint(session_bp)
    
    # 应用健康检查端点
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'AI语音助手服务运行中'}
    
    @app.route('/')
    def index():
        # index.html 应该在 backend/templates/index.html
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 