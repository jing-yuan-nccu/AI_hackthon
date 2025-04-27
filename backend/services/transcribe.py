import boto3
import time
import json
import logging
from botocore.exceptions import ClientError

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscribeService:
    def __init__(self, region='us-west-2'):
        """
        初始化 Transcribe 服務
        """
        self.client = boto3.client('transcribe', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = 'crossover-audio'  # 替換為您的 S3 bucket 名稱
        
    def upload_file_to_s3(self, file_path, object_name=None):
        """
        上傳本地文件到 S3
        
        Args:
            file_path (str): 本地文件路徑
            object_name (str): S3 對象名稱
        """
        if object_name is None:
            object_name = file_path.split('/')[-1]
            
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            logger.info(f"文件成功上傳到 S3: {object_name}")
            return f"s3://{self.bucket_name}/{object_name}"
        except ClientError as e:
            logger.error(f"上傳文件失敗: {str(e)}")
            raise

    def start_transcription(self, job_name, file_uri, language_code='zh-TW'):
        """
        開始轉錄任務
        
        Args:
            job_name (str): 轉錄任務名稱
            file_uri (str): S3 文件 URI
            language_code (str): 語言代碼
        """
        try:
            response = self.client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': file_uri},
                MediaFormat='wav',  # 根據您的音頻格式調整
                LanguageCode=language_code
            )
            logger.info(f"轉錄任務已開始: {job_name}")
            return response
        except ClientError as e:
            logger.error(f"開始轉錄任務失敗: {str(e)}")
            raise

    def get_transcription_result(self, job_name):
        """
        獲取轉錄結果
        
        Args:
            job_name (str): 轉錄任務名稱
        """
        try:
            while True:
                response = self.client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status in ['COMPLETED', 'FAILED']:
                    break
                    
                logger.info(f"任務狀態: {status}")
                time.sleep(5)
            
            if status == 'COMPLETED':
                result_url = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                # 下載並解析結果
                import urllib.request
                response = urllib.request.urlopen(result_url)
                data = json.loads(response.read())
                return data['results']['transcripts'][0]['transcript']
            else:
                logger.error(f"轉錄任務失敗: {response['TranscriptionJob']['FailureReason']}")
                return None
                
        except ClientError as e:
            logger.error(f"獲取轉錄結果失敗: {str(e)}")
            raise