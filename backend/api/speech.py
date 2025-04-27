"""
语音API模块 - 处理语音相关的API端点
"""
import os
import uuid
import time
import logging
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from services.transcribe import TranscribeService
from services.bedrock import BedrockService

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
speech_bp = Blueprint('speech', __name__, url_prefix='/api')

# 初始化服务
transcribe_service = None
bedrock_service = None

@speech_bp.before_app_first_request
def init_services():
    """在第一个请求前初始化服务"""
    global transcribe_service,  bedrock_service
    region = current_app.config.get('AWS_REGION')
    model_id = current_app.config.get('AWS_BEDROCK_MODEL')
    
    transcribe_service = TranscribeService(region)
    bedrock_service = BedrockService(region, model_id)
    
    logger.info(f"已初始化语音服务，区域: {region}")


@speech_bp.route('/transcribe', methods=['POST'])
def transcribe():
    """
    转录端点 - 将音频转换为文本
    
    请求:
        包含audio文件的表单数据
        
    返回:
        JSON对象，包含转录文本
    """
    try:
        # 初始化服务(如果尚未初始化)
        global transcribe_service
        if transcribe_service is None:
            init_services()
            
        # 检查是否有音频文件
        if 'audio' not in request.files:
            return jsonify({"error": "未提供音频文件"}), 400
            
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"error": "未选择文件"}), 400

        # 獲取當前文件所在目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 往上一級到 backend 目錄
        backend_dir = os.path.dirname(current_dir)
        # 創建 audio_file 目錄路徑
        audio_dir = os.path.join(backend_dir, "audio_file")
        # 確保目錄存在
        os.makedirs(audio_dir, exist_ok=True)
        # 創建音頻文件路徑
        audio_path = os.path.join(audio_dir, f"{uuid.uuid4()}.wav")
        # 保存音頻文件
        audio_file.save(audio_path)
        
        # 转录音频
        try:
            # 初始化服務
            transcribe = TranscribeService()            
            # 生成唯一的任務名稱
            job_name = f"test-transcribe-{int(time.time())}"
            
            # 上傳文件到 S3
            logger.info("上傳文件到 S3...")
            s3_uri = transcribe.upload_file_to_s3(audio_path)
            
            # 開始轉錄
            logger.info("開始轉錄...")
            transcribe.start_transcription(job_name, s3_uri)
            
            # 獲取結果
            logger.info("等待轉錄結果...")
            result = transcribe.get_transcription_result(job_name)
            
            if result:
                logger.info("轉錄完成！")
                logger.info(f"轉錄結果: {result}")
            else:
                logger.error("轉錄失敗")
                
        except Exception as e:
            logger.error(f"測試過程中發生錯誤: {str(e)}")
        return jsonify({"text": result})
        
    except Exception as e:
        logger.error(f"转录处理出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

