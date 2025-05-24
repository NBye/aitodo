import IDate from "./IDate";
import WavEncoder from 'wav-encoder';
export default class RecordAudio {

    constructor() {
        this._chunks = [];
        this._recorder = null;
        this.ext = 'wva';
        this.recording = false;
    }

    async start(done = null) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this._recorder = new MediaRecorder(stream);
        // 当录音数据可用时将其存储
        this._recorder.ondataavailable = (event) => {
            this._chunks.push(event.data);
        };
        // 录音停止时处理录音文件
        this._recorder.onstop = async () => {
            let type = { type: 'audio/webm' }
            let blob = new Blob(this._chunks, type);
            let name = `录音v${IDate.format('yyyymmddhhiiss')}`
            let file = new File([blob], `${name}.wav`, type);
            let audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let arrayBuffer = await file.arrayBuffer();
            let audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            let audioData = await WavEncoder.encode({
                sampleRate: audioBuffer.sampleRate,
                channelData: Array.from({ length: audioBuffer.numberOfChannels }).map((_, i) => audioBuffer.getChannelData(i)),
            });
            blob = new Blob([audioData], { type: 'audio/wav' });
            this.file = new File([blob], `${name}.wav`, type);
            this.ext = 'wav'
            if (typeof done == 'function') {
                done(this)
            }
        };
        this._recorder.start();
        this.recording = true;
    }

    stop() {
        this._recorder.stop();
        this.recording = false;

        // 停止麦克风流
        let tracks = this._recorder.stream.getTracks();
        tracks.forEach(track => track.stop());  // 停止流中的每个轨道
    }
}
