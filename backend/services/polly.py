"""
本地文字轉語音服務 - 將文字轉換為語音
"""
import os
import uuid
import logging
import tempfile
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class PollyService:
    """本地文字轉語音服務封裝類"""
    
    def __init__(self, region=None):
        """
        初始化文字轉語音服務
        
        Args:
            region (str): 區域參數 (為了與原API保持兼容，但在本地模式下不使用)
        """
        # 設置輸出目錄
        self.output_dir = os.environ.get('AUDIO_DIR', os.path.join(tempfile.gettempdir(), 'audio_output'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 檢查是否有本地TTS工具
        self.has_gtts = self._check_gtts()
        
        logger.info(f"初始化本地文字轉語音服務，輸出目錄: {self.output_dir}, gTTS可用: {self.has_gtts}")
    
    def _check_gtts(self):
        """檢查是否安裝了gTTS庫"""
        try:
            import gtts
            return True
        except ImportError:
            logger.warning("未檢測到gTTS庫，將使用基本模擬模式")
            return False
    
    def synthesize_speech(self, text, output_path, voice_id=None, output_format='mp3'):
        """
        將文字合成為語音並保存到文件
        
        Args:
            text (str): 要合成的文字
            output_path (str): 輸出音頻文件路徑
            voice_id (str): 語音ID，在本地模式下不使用
            output_format (str): 輸出格式，默認為'mp3'
            
        Returns:
            bool: 合成是否成功
        """
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            logger.info(f"合成語音，文字長度: {len(text)}")
            
            # 使用gTTS合成語音 (如果可用)
            if self.has_gtts:
                return self._synthesize_with_gtts(text, output_path)
            else:
                # 使用模擬模式
                return self._mock_synthesize_speech(text, output_path)
                
        except Exception as e:
            logger.error(f"語音合成失敗: {str(e)}")
            self._create_empty_audio(output_path)
            return False
    
    def _synthesize_with_gtts(self, text, output_path):
        """使用Google Text-to-Speech合成語音"""
        try:
            from gtts import gTTS
            
            # 使用gTTS合成語音
            tts = gTTS(text=text, lang='zh-tw', slow=False)
            tts.save(output_path)
            
            logger.info(f"使用gTTS合成語音成功: {output_path}")
            return True
        except Exception as e:
            logger.error(f"gTTS合成失敗: {str(e)}")
            return self._mock_synthesize_speech(text, output_path)
    
    def _mock_synthesize_speech(self, text, output_path):
        """
        模擬語音合成（用於開發和測試）
        
        Args:
            text (str): 要合成的文字
            output_path (str): 輸出音頻文件路徑
            
        Returns:
            bool: 合成是否成功
        """
        try:
            logger.warning(f"使用模擬模式合成語音: '{text[:30]}...'")
            
            # 創建一個最小的有效MP3文件
            self._create_empty_audio(output_path)
            
            logger.info(f"模擬語音合成完成，文件: {output_path}")
            return True
        except Exception as e:
            logger.error(f"模擬語音合成失敗: {str(e)}")
            return False
    
    def _create_empty_audio(self, output_path):
        """創建一個空的音頻文件"""
        with open(output_path, 'wb') as file:
            # 寫入一個最小的有效MP3文件頭
            file.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')