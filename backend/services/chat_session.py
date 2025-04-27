"""
聊天會話管理模块 - 處理对话历史记录
"""
import time
import uuid
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class ChatSession:
    """聊天會話管理類"""
    
    def __init__(self, session_id=None, max_history=20, max_idle_time=3600):
        """
        初始化聊天會話
        
        Args:
            session_id (str): 會話ID, 如果為None則自動生成
            max_history (int): 歷史記錄保存的最大消息數量
            max_idle_time (int): 最大空閒時間(秒), 超過此時間的會話可被清理
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.max_history = max_history
        self.messages = []
        self.last_active = time.time()
        self.max_idle_time = max_idle_time
    
    def add_message(self, role, content):
        """
        添加消息到會話歷史
        
        Args:
            role (str): 消息角色, 例如 'user' 或 'assistant'
            content (str): 消息內容
        """
        self.messages.append({"role": role, "content": content})
        self.last_active = time.time()
        
        # 保持歷史不超過最大長度
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context(self):
        """
        獲取完整的對話上下文
        
        Returns:
            list: 消息列表, 格式為 [{"role": "...", "content": "..."}, ...]
        """
        return self.messages
    
    def clear_history(self):
        """清空歷史記錄"""
        self.messages = []
        self.last_active = time.time()
    
    def is_expired(self):
        """
        檢查會話是否已過期
        
        Returns:
            bool: 如果會話已過期則返回True
        """
        return (time.time() - self.last_active) > self.max_idle_time

class ChatSessionManager:
    """聊天會話管理器"""
    
    def __init__(self, max_sessions=1000, cleanup_interval=3600):
        """
        初始化聊天會話管理器
        
        Args:
            max_sessions (int): 同時維護的最大會話數量
            cleanup_interval (int): 清理過期會話的間隔時間(秒)
        """
        self.sessions = {}
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
    
    def get_session(self, session_id=None):
        """
        獲取或創建會話
        
        Args:
            session_id (str): 會話ID, 如果不存在則創建新會話
            
        Returns:
            ChatSession: 會話對象
        """
        # 嘗試清理過期會話
        self._try_cleanup()
        
        # 如果沒有提供session_id或提供的id不存在, 創建新會話
        if session_id is None or session_id not in self.sessions:
            # 如果會話數量達到上限, 清理過期會話
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_expired()
            
            # 如果還是達到上限, 移除最老的會話
            if len(self.sessions) >= self.max_sessions:
                self._remove_oldest()
            
            # 創建新會話
            session = ChatSession(session_id)
            self.sessions[session.session_id] = session
            logger.info(f"創建新會話: {session.session_id}")
            return session
        
        # 返回現有會話
        self.sessions[session_id].last_active = time.time()
        return self.sessions[session_id]
    
    def delete_session(self, session_id):
        """
        刪除會話
        
        Args:
            session_id (str): 要刪除的會話ID
            
        Returns:
            bool: 是否成功刪除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"刪除會話: {session_id}")
            return True
        return False
    
    def _try_cleanup(self):
        """定期嘗試清理過期會話"""
        if (time.time() - self.last_cleanup) > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = time.time()
    
    def _cleanup_expired(self):
        """清理所有過期會話"""
        expired_ids = [sid for sid, session in self.sessions.items() if session.is_expired()]
        for sid in expired_ids:
            del self.sessions[sid]
        
        if expired_ids:
            logger.info(f"清理了 {len(expired_ids)} 個過期會話")
    
    def _remove_oldest(self):
        """移除最老(最長時間未活動)的會話"""
        if not self.sessions:
            return
            
        oldest_id = min(self.sessions.items(), key=lambda x: x[1].last_active)[0]
        del self.sessions[oldest_id]
        logger.info(f"移除最老的會話: {oldest_id}")

# 全局會話管理器實例
session_manager = ChatSessionManager()