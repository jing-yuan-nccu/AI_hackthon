import boto3
import json
from config import Config
import logging

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self, region=Config.AWS_REGION, model_id=Config.AWS_BEDROCK_MODEL):
        self.client = boto3.client(
            "bedrock-runtime", 
            region_name='us-west-2'
        )
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

    def chat(self, prompt, conversation_history=None):
        """
        使用 Bedrock 生成回應
        
        Args:
            prompt (str): 輸入文本
        Returns:
            str: 生成的回應
        """
        try:
            # 準備消息列表
            messages = []
            
            # 如果有對話歷史，加入到消息列表
            if conversation_history:
                messages.extend(conversation_history)
            
            # 如果沒有歷史或歷史中最後一條不是本次的用戶輸入，則添加當前用戶輸入
            if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != prompt:
                messages.append({"role": "user", "content": prompt})
            
            # Claude 的請求格式
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
            }

            # 調用模型
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            # 解析回應
            response_body = json.loads(response.get('body').read())
            
            # 根據回應格式提取文本
            if isinstance(response_body, dict):
                return response_body.get('content', [{}])[0].get('text', '')
            
            return str(response_body)

        except Exception as e:
            logger.error(f"Bedrock API 調用失敗: {str(e)}")
            raise

    def generate_text(self, prompt, session_id=None, conversation_history=None):
        """
        生成文本的包裝方法
        """
        from services.chat_session import session_manager
        if session_id and not conversation_history:
            session = session_manager.get_session(session_id)
            conversation_history = session.get_context()
            
            # 臨時添加當前提示到歷史，以便LLM處理
            temp_history = conversation_history + [{"role": "user", "content": prompt}]
            print("history:", temp_history)
            response = self.chat(prompt, temp_history)
            
            # 將用戶提示和AI回應添加到會話中
            session.add_message("user", prompt)
            session.add_message("assistant", response)
            
            return response
        else:
            # 直接調用chat方法
            print("【BEDROCK】无会话ID或提供了自定义历史，直接调用chat")
            return self.chat(prompt, conversation_history)
