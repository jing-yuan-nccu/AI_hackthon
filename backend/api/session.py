"""
会话管理API模块 - 处理会话创建、获取和删除
"""
import logging
from flask import Blueprint, request, jsonify
from services.chat_session import session_manager
# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
session_bp = Blueprint('session', __name__, url_prefix='/api/session')

@session_bp.route('', methods=['POST'])
def create_get_session():
    """
    创建或获取会话
    
    请求参数:
        session_id (str, 可选): 现有会话ID
        
    返回:
        JSON对象，包含会话ID和消息数量
    """
    try:
        # 获取请求数据
        data = request.json or {}
        session_id = data.get('session_id')
        
        # 获取或创建会话
        session = session_manager.get_session(session_id)
        
        return jsonify({
            "session_id": session.session_id,
            "message_count": len(session.get_context())
        })
        
    except Exception as e:
        logger.error(f"创建/获取会话出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@session_bp.route('', methods=['DELETE'])
def delete_session():
    """
    删除会话
    
    请求参数:
        session_id (str): 要删除的会话ID
        
    返回:
        JSON对象，包含操作状态
    """
    try:
        # 获取请求数据
        data = request.json or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "未提供会话ID"}), 400
        
        # 删除会话
        success = session_manager.delete_session(session_id)
        
        if success:
            return jsonify({"status": "success", "message": "会话已删除"})
        else:
            return jsonify({"error": "未找到指定会话"}), 404
            
    except Exception as e:
        logger.error(f"删除会话出错: {str(e)}")
        return jsonify({"error": str(e)}), 500