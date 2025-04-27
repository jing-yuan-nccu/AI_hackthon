# backend/test_llm.py

import pytest
from flask import Flask
from api.llm import llm_bp, bedrock_service as global_service
import services.bedrock as bedrock_module

@pytest.fixture
def client(monkeypatch):
    # 建立測試用 Flask app
    app = Flask(__name__)
    app.config['AWS_REGION'] = 'us-east-1'
    app.config['AWS_BEDROCK_MODEL'] = 'test-model-id'
    app.register_blueprint(llm_bp)

    # 用 DummyService 取代真正的 BedrockService
    class DummyService:
        def __init__(self, region, model_id):
            # 確認 init_services 傳入了正確參數
            assert region == 'us-east-1'
            assert model_id == 'test-model-id'
        def chat(self, prompt):
            return f"Echo: {prompt}"

    monkeypatch.setattr(
        bedrock_module,
        'BedrockService',
        DummyService
    )

    # 每次測試前清掉全域 service（模擬尚未初始化）
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_BEDROCK_MODEL', 'test-model-id')
    # 重置全域變數
    monkeypatch.setattr('api.llm.bedrock_service', None)

    return app.test_client()

def test_process_text_success(client):
    resp = client.post('/api/llm',
                       json={'prompt': 'hello world'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'response' in body
    assert body['response'] == 'Echo: hello world'

def test_process_text_missing_prompt(client):
    resp = client.post('/api/llm', json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body == {"error": "未提供提示内容"}

def test_process_text_service_error(client, monkeypatch):
    # 模擬 service.chat 拋例外
    class BrokenService:
        def __init__(self, region, model_id): pass
        def chat(self, prompt):
            raise RuntimeError("failure")
    monkeypatch.setattr(
        bedrock_module,
        'BedrockService',
        BrokenService
    )
    # 清空已初始化的 service
    monkeypatch.setattr('api.llm.bedrock_service', None)

    resp = client.post('/api/llm', json={'prompt': 'test'})
    assert resp.status_code == 500
    body = resp.get_json()
    assert 'error' in body
    assert "failure" in body['error']
