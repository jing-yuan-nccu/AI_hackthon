/**
 * AI 语音助手 - 主应用逻辑
 * 使用 apiService 处理 API 通信
 */

document.addEventListener('DOMContentLoaded', () => {
    window.apiService.getSession().catch(error => {
        console.error('获取会话失败:', error);
        addMessage('system', '会话初始化失败，部分功能可能无法正常工作。');
    });
    // DOM 元素
    const chatMessages = document.getElementById('chat-messages');
    const recordButton = document.getElementById('record-button');
    const recordingIndicator = document.getElementById('recording-indicator');
    const statusElement = document.getElementById('status');
    const textInput = document.getElementById('text-input');
    const sendButton = document.getElementById('send-button');
    const audioPlayer = document.getElementById('audio-player');
    const connectionStatus = document.getElementById('connection-status');
    const themeToggle = document.getElementById('theme-toggle');
    const clearChatButton = document.getElementById('clear-chat');
    const settingsButton = document.getElementById('settings-button');
    const volumeControl = document.getElementById('volume-control');

    // 录音相关
    let isRecording = false;
    let audioRecorder = new AudioRecorder();
    let recordedAudio = null;
    
    // 状态管理
    let isProcessing = false;
    let conversationHistory = [];
    
    // 音频设置
    let volume = localStorage.getItem('voiceAssistantVolume') || 0.8;
    if (volumeControl) {
        volumeControl.value = volume * 100;
        volumeControl.addEventListener('change', function() {
            volume = this.value / 100;
            localStorage.setItem('voiceAssistantVolume', volume);
            audioPlayer.volume = volume;
        });
    }
    
    // 初始化
    checkConnection();
    setInterval(checkConnection, 30000); // 每30秒检查一次连接状态
    
    if (themeToggle) {
        console.log('Theme toggle found in app.js');
        
        // 直接设置点击处理函数
        themeToggle.onclick = function() {
          console.log('Theme toggle clicked');
          
          // 切换主题类
          document.body.classList.toggle('dark-theme');
          
          // 切换图标
          const icon = this.querySelector('i');
          if (icon) {
            // 直接根据当前主题设置完整的类名
            const isDark = document.body.classList.contains('dark-theme');
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
          }
          
          // 保存设置
          const theme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
          localStorage.setItem('voiceAssistantTheme', theme);
        };
        
        // 应用保存的主题
        const savedTheme = localStorage.getItem('voiceAssistantTheme') || 'light';
        document.body.classList.toggle('dark-theme', savedTheme === 'dark');
        
        // 设置正确的图标
        const icon = themeToggle.querySelector('i');
        if (icon && savedTheme === 'dark') {
          icon.className = 'fas fa-sun';
        }
      }
    
    // 清除聊天记录
    if (clearChatButton) {
        clearChatButton.addEventListener('click', () => {
            if (confirm('确定要清除所有聊天记录吗？')) {
                chatMessages.innerHTML = '';
                conversationHistory = [];
                window.apiService.clearCurrentSession()
                    .then(() => {
                        addMessage('system', '聊天记录已清除。你好，我是你的AI语音助手，有什么可以帮你的？');
                    })
                    .catch(error => {
                        console.error('清除会话失败:', error);
                        addMessage('system', '清除会话失败，部分功能可能无法正常工作。');
                    });
            }
        });
    }

    // 录音按钮事件
    recordButton.addEventListener('click', () => {
        if (isProcessing) {
            showStatus('请等待上一条消息处理完成');
            return;
        }
        
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    // 发送文字按钮事件
    sendButton.addEventListener('click', () => {
        sendTextMessage();
    });

    // 文字输入框回车事件
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    });

    /**
     * 开始录音
     */
    function startRecording() {
        audioRecorder.start()
            .then(() => {
                isRecording = true;
                recordButton.classList.add('recording');
                recordingIndicator.classList.add('active');
                showStatus('正在录音...');
            })
            .catch(error => {
                console.error('录音失败:', error);
                showStatus('无法访问麦克风');
            });
    }

    /**
     * 停止录音
     */
    function stopRecording() {
        audioRecorder.stop()
            .then(audioBlob => {
                isRecording = false;
                recordButton.classList.remove('recording');
                recordingIndicator.classList.remove('active');
                showStatus('录音完成，正在处理...');
                recordedAudio = audioBlob;
                processAudioInput(audioBlob);
            })
            .catch(error => {
                console.error('停止录音失败:', error);
                showStatus('录音处理失败');
                isRecording = false;
                recordButton.classList.remove('recording');
                recordingIndicator.classList.remove('active');
            });
    }

    /**
     * 处理录音输入
     * @param {Blob} audioBlob - 录音得到的音频数据
     */
    async function processAudioInput(audioBlob) {
        if (isProcessing) return;
        
        isProcessing = true;
        
        try {
            // 首先进行语音转文字
            const transcribeResult = await window.apiService.transcribeAudio(audioBlob);
            
            if (transcribeResult.text && transcribeResult.text.trim() !== '') {
                // 显示用户输入
                addMessage('user', transcribeResult.text);
                
                // 显示AI正在思考的指示器
                showTypingIndicator();
                
                // 将录音发送到语音聊天接口获取回复
                const chatResult = await window.apiService.getLlmResponse(transcribeResult);
                // **打印整个 chatResult**
                // 移除"正在输入"指示器
                removeTypingIndicator();
                // 然后再取出你需要的字段
                const replyText = chatResult.response;  // 或者 chatResult.text
                // 添加AI回复消息
                addMessage('assistant', replyText);
            } else {
                throw new Error('未能识别语音内容');
            }
            
            showStatus('准备就绪');
        } catch (error) {
            console.error('处理失败:', error);
            removeTypingIndicator();
            showStatus(`出错: ${error.message}`);
            
            // 如果是语音识别失败，添加系统消息提示用户
            if (error.message.includes('未能识别')) {
                addMessage('system', '抱歉，我没有听清楚您说的内容，请再试一次。');
            }
        } finally {
            isProcessing = false;
        }
    }

    /**
     * 发送文本消息
     */
    async function sendTextMessage() {
        const text = textInput.value.trim();
        if (text === '' || isProcessing) return;
        
        isProcessing = true;
        textInput.value = '';
        
        try {
            // 添加用户消息
            addMessage('user', text);
            
            // 显示AI正在思考的指示器
            showTypingIndicator();
            
            // 获取LLM响应
            const result = await window.apiService.getLlmResponse(text);
            
            // 移除"正在输入"指示器
            removeTypingIndicator();
            
            // 添加AI回复消息
            if (result.response) {
                addMessage('assistant', result.response);
            } else {
                addMessage('system', '未能获取有效回复');
            }
            
            showStatus('准备就绪');
        } catch (error) {
            console.error('处理失败:', error);
            removeTypingIndicator();
            showStatus(`出错: ${error.message}`);
            addMessage('system', '抱歉，处理您的请求时出现了问题。请稍后再试。');
        } finally {
            isProcessing = false;
        }
    }

    /**
     * 添加消息到聊天界面
     * @param {string} type - 消息类型: 'user', 'assistant', 或 'system'
     * @param {string} content - 消息内容
     */
    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // 处理消息内容，可以支持简单的 Markdown 格式
        const formattedContent = formatMessage(content);
        contentDiv.innerHTML = formattedContent;
        
        // 添加时间戳
        if (type !== 'system') {
            const timestamp = document.createElement('div');
            timestamp.className = 'message-timestamp';
            timestamp.textContent = getTimeString();
            contentDiv.appendChild(timestamp);
        }
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // 保存到历史记录
        conversationHistory.push({ role: type, content: content });
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    /**
     * 格式化消息内容
     * @param {string} content - 原始消息内容
     * @returns {string} - 格式化后的HTML
     */
    function formatMessage(content) {
        // 转义HTML
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // 处理简单的Markdown格式
        // 粗体
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // 斜体
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // 代码
        formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
        // 换行
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    /**
     * 获取当前时间字符串
     * @returns {string} - 时间字符串，格式为 "HH:MM"
     */
    function getTimeString() {
        const now = new Date();
        return now.getHours().toString().padStart(2, '0') + ':' + 
               now.getMinutes().toString().padStart(2, '0');
    }

    /**
     * 显示"正在输入"指示器
     */
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator-container';
        
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            indicatorDiv.appendChild(dot);
        }
        
        typingDiv.appendChild(indicatorDiv);
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * 移除"正在输入"指示器
     */
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator-container');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * 播放音频
     * @param {string} audioUrl - 音频URL
     */
    function playAudio(audioUrl) {
        audioPlayer.volume = volume;
        audioPlayer.src = audioUrl;
        audioPlayer.play().catch(error => {
            console.error('播放音频失败:', error);
        });
    }

    /**
     * 显示状态信息
     * @param {string} message - 状态消息
     */
    function showStatus(message) {
        statusElement.textContent = message;
    }

    /**
     * 检查服务器连接状态
     */
    async function checkConnection() {
        try {
            const isConnected = await window.apiService.checkHealth();
            connectionStatus.textContent = isConnected ? '已连接' : '未连接';
            connectionStatus.className = isConnected ? 'connected' : 'disconnected';
        } catch (error) {
            console.error('服务器连接检查失败:', error);
            connectionStatus.textContent = '未连接';
            connectionStatus.className = 'disconnected';
        }
    }
    
    // 初始欢迎消息
    addMessage('system', '你好！我是你的 AI 语音助手。请点击下方麦克风按钮开始对话，或直接输入文字。');
});