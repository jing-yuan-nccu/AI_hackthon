/**
 * 音频录制类 - 处理浏览器音频录制功能
 */
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
    }

    /**
     * 开始录音
     * @returns {Promise} - 录音开始后的Promise
     */
    async start() {
        try {
            // 请求麦克风访问权限
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // 创建MediaRecorder实例
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];
            
            // 设置数据处理
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            // 开始录音
            this.mediaRecorder.start();
            console.log('开始录音...');
            
            return Promise.resolve();
        } catch (error) {
            console.error('启动录音失败:', error);
            return Promise.reject(error);
        }
    }

    /**
     * 停止录音
     * @returns {Promise<Blob>} - 包含录音数据的Promise
     */
    stop() {
        return new Promise((resolve, reject) => {
            try {
                if (!this.mediaRecorder) {
                    reject(new Error('录音未开始'));
                    return;
                }
                
                // 设置录音停止后的处理
                this.mediaRecorder.onstop = () => {
                    // 停止所有音频轨道
                    if (this.stream) {
                        this.stream.getTracks().forEach(track => track.stop());
                    }
                    
                    // 创建音频Blob
                    const audioBlob = new Blob(this.audioChunks, { 
                        type: 'audio/webm' 
                    });
                    
                    console.log('录音完成，数据大小:', audioBlob.size);
                    resolve(audioBlob);
                };
                
                // 停止录音
                this.mediaRecorder.stop();
            } catch (error) {
                console.error('停止录音失败:', error);
                reject(error);
            }
        });
    }
}