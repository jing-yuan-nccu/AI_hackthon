/**
 * AI 语音助手 - API 通信模块
 * 处理与后端 API 的所有通信
 */

class ApiService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl; // 如果前后端不在同一域，可以设置基础URL
        this.endpoints = {
            transcribe: '/api/transcribe',
            llm: '/api/llm',
            voiceChat: '/api/voice-chat',
            health: '/api/health',
            session: '/api/session'
        };

        // 初始化会话ID (从localStorage中读取，以保持会话持久化)
        this.sessionId = localStorage.getItem('voiceAssistantSessionId') || null;
    }

    /**
     * 检查服务器健康状态
     * @returns {Promise<boolean>} - 服务器是否健康
     */
    async checkHealth() {
        try {
            const response = await fetch(this.baseUrl + this.endpoints.health);
            return response.ok;
        } catch (error) {
            console.error('健康检查失败:', error);
            return false;
        }
    }
    /**
     * 获取或创建会话
     * @param {string} sessionId - 可选会话ID
     * @returns {Promise<Object>} - 包含会话信息的对象
     */
    async getSession(sessionId = null) {
        try {
            const response = await fetch(this.baseUrl + this.endpoints.session, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId || this.sessionId })
            });
            
            if (!response.ok) {
                throw new Error(`创建会话失败: ${response.status}`);
            }
            
            const result = await response.json();
            this.sessionId = result.session_id;
            
            // 保存会话ID到本地存储
            localStorage.setItem('voiceAssistantSessionId', this.sessionId);
            
            return result;
        } catch (error) {
            console.error('获取会话失败:', error);
            throw error;
        }
    }
    
    /**
     * 删除会话
     * @param {string} sessionId - 要删除的会话ID
     * @returns {Promise<Object>} - 操作结果
     */
    async deleteSession(sessionId = null) {
        try {
            const targetSessionId = sessionId || this.sessionId;
            
            if (!targetSessionId) {
                throw new Error('未提供会话ID');
            }
            
            const response = await fetch(this.baseUrl + this.endpoints.session, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: targetSessionId })
            });
            
            if (!response.ok) {
                throw new Error(`删除会话失败: ${response.status}`);
            }
            
            // 如果删除的是当前会话，清除本地存储的会话ID
            if (targetSessionId === this.sessionId) {
                this.sessionId = null;
                localStorage.removeItem('voiceAssistantSessionId');
            }
            
            return await response.json();
        } catch (error) {
            console.error('删除会话失败:', error);
            throw error;
        }
    }
    /**
     * 将语音转换为文字
     * @param {Blob} audioBlob - 音频数据
     * @returns {Promise<Object>} - 包含转写文本的对象
     */
    async transcribeAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            if (this.sessionId) {
                formData.append('session_id', this.sessionId);
            }
            
            const response = await fetch(this.baseUrl + this.endpoints.transcribe, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`语音转文字失败: ${response.status}`);
            }

            const result = await response.json();

            if (result.session_id) {
                this.sessionId = result.session_id;
                localStorage.setItem('voiceAssistantSessionId', this.sessionId);
            }
            
            return result;
        } catch (error) {
            console.error('语音转文字请求失败:', error);
            throw error;
        }
    }

    /**
     * 发送语音到语音聊天接口
     * @param {Blob} audioBlob - 音频数据
     * @returns {Promise<Object>} - 包含AI文本回复的对象
     */
    async voiceChatWithAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch(this.baseUrl + this.endpoints.voiceChat, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`语音聊天请求失败: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('语音聊天请求失败:', error);
            throw error;
        }
    }

    /**
     * 获取大语言模型的回复
     * @param {string} prompt - 用户输入的文本
     * @returns {Promise<Object>} - 包含AI回复的对象
     */
    async getLlmResponse(prompt) {
        try {
            if (!this.sessionId) {
                await this.getSession();
            }

            const response = await fetch(this.baseUrl + this.endpoints.llm, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8'
                },
                body: JSON.stringify({ 
                    prompt,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`获取AI回复失败: ${response.status}`);
            }

            const result = await response.json();

            if (result.session_id) {
                this.sessionId = result.session_id;
                localStorage.setItem('voiceAssistantSessionId', this.sessionId);
            }
            return result;
        } catch (error) {
            console.error('获取AI回复失败:', error);
            throw error;
        }
    }
    
    /**
     * 处理完整的文本对话流程
     * @param {string} text - 用户输入的文本
     * @returns {Promise<Object>} - 包含AI文本回复的对象
     */
    async processTextConversation(text) {
        try {
            // 获取AI文本回复
            const llmResponse = await this.getLlmResponse(text);
            
            if (!llmResponse.response) {
                throw new Error('未获取到AI回复');
            }
            
            // 返回结果
            return {
                text: llmResponse.response,
                session_id: llmResponse.sessionId,
                messages: llmResponse.messages_count
            };
        } catch (error) {
            console.error('文本对话处理失败:', error);
            throw error;
        }
    }
    /**
     * 清除当前会话历史
     */
    async clearCurrentSession() {
        try {
            if (this.sessionId) {
                await this.deleteSession();
                // 创建新会话
                await this.getSession();
                return { success: true };
            }
            return { success: false, reason: "no_active_session" };
        } catch (error) {
            console.error('清除会话失败:', error);
            throw error;
        }
    }
}

// 导出ApiService实例
window.apiService = new ApiService();