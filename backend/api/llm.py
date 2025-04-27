"""
LLM API模块 - 处理与LLM相关的API端点
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from services.bedrock import BedrockService

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

# 初始化服务
bedrock_service = None

@llm_bp.before_app_first_request
def init_services():
    """在第一个请求前初始化服务"""
    global bedrock_service
    region = current_app.config.get('AWS_REGION')
    model_id = current_app.config.get('AWS_BEDROCK_MODEL')
    bedrock_service = BedrockService(region, model_id)
    logger.info(f"已初始化Bedrock服务，区域: {region}, 模型: {model_id}")

@llm_bp.route('', methods=['POST'])
def process_text():
    """
    处理文本请求，调用LLM生成回答
    
    请求参数:
        prompt (str): 用户提示文本
        
    返回:
        JSON对象，包含生成的回答
    """
    try:
        # 获取请求数据
        data = request.get_json()
        print("【LLM API】收到请求数据:", data)  # 添加调试信息
        
        if not data or 'prompt' not in data:
            return jsonify({"error": "未提供提示内容"}), 400
            
        p = data.get('prompt')
        session_id = data.get('session_id')
        print("【LLM API】收到会话ID:", session_id)  # 添加调试信息

        if isinstance(p, dict) and 'text' in p:
            prompt = p['text']
        else:
            prompt = str(p)
        logger.info(f"收到LLM请求，提示: {prompt[:50]}...")
        
        # 调用Bedrock服务
        global bedrock_service
        if bedrock_service is None:
            init_services()
            
        response = bedrock_service.generate_text(prompt, session_id)
        logger.info(f"LLM已生成回答，长度: {len(response)}")
        
        # 返回结果
        return jsonify({"response": response, 
                        "session_id": session_id,
                        "messages_count": len(response)
                        })
        
    except Exception as e:
        logger.error(f"处理LLM请求时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

