class MyAIGist {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordingTimer = null;
        this.startTime = null;
        this.currentRecordingBlob = null;
        this.selectedSummaryLevel = 'standard'; // Default to standard

        // Bind methods (extra safety against "not a function" if something rebinds context)
        this.processContent = this.processContent.bind(this);
        this.askQuestion = this.askQuestion.bind(this);

        this.init();
    }

    init() {
        console.log('🚀 Initializing MyAIGist...');
        this.setupEventListeners();
        this.setupTabs();
        this.setupSummaryLevels();

        // Debug: list methods to ensure processContent exists
        const protoMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(this));
        console.log('🧩 Methods on instance:', protoMethods);
    }

    setupEventListeners() {
        // Content processing
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.processContent();
            });
        }

        // Q&A
        const askBtn = document.getElementById('ask-btn');
        if (askBtn) {
            askBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.askQuestion();
            });
        }

        // Microphone button
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🎤 Mic button clicked, isRecording:', this.isRecording);
                this.toggleRecording();
            });
        }

        // Transcribe recorded audio
        const transcribeBtn = document.getElementById('transcribe-btn');
        if (transcribeBtn) {
            transcribeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.transcribeRecording();
            });
        }

        // Re-record button
        const rerecordBtn = document.getElementById('re-record-btn');
        if (rerecordBtn) {
            rerecordBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.startNewRecording();
            });
        }

        // Enter key for questions
        const questionInput = document.getElementById('question-text');
        if (questionInput) {
            questionInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.askQuestion();
                }
            });
        }

        // ✅ File input filename display
        const fileInput = document.getElementById('file-input');
        const fileNameEl = document.getElementById('file-name');
        if (fileInput && fileNameEl) {
            fileInput.addEventListener('change', () => {
                const name = fileInput.files && fileInput.files[0] ? fileInput.files[0].name : 'No file chosen';
                fileNameEl.textContent = name;
            });
        }
    }

    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanels = document.querySelectorAll('.tab-panel');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;

                tabBtns.forEach(b => b.classList.remove('active'));
                tabPanels.forEach(p => p.classList.remove('active'));

                btn.classList.add('active');
                const panel = document.getElementById(`${tabName}-tab`);
                if (panel) panel.classList.add('active');
            });
        });
    }

    setupSummaryLevels() {
        const summaryBtns = document.querySelectorAll('.summary-btn');

        summaryBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const level = btn.dataset.level;
                console.log('📋 Summary level selected:', level);

                // Update selected level
                this.selectedSummaryLevel = level;

                // Update UI
                summaryBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
                this.showStatus(`Summary level set to: ${levelNames[level]}`, 'success');
            });
        });
    }

    // ===== Recording methods (unchanged) =====
    async toggleRecording() {
        console.log('🔄 Toggle recording called, current state:', this.isRecording);
        if (this.isRecording) this.stopRecording();
        else await this.startRecording();
    }

    async startRecording() {
        console.log('▶️ Starting recording...');
        try {
            this.hidePlaybackSection();

            console.log('🎤 Requesting microphone access...');
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { sampleRate: 44100, channelCount: 1, echoCancellation: true, noiseSuppression: true }
            });
            console.log('✅ Microphone access granted');

            this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

            this.audioChunks = [];
            this.startTime = Date.now();

            this.mediaRecorder.ondataavailable = (event) => {
                console.log('📦 Audio data available:', event.data.size, 'bytes');
                if (event.data.size > 0) this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                console.log('⏹️ MediaRecorder stopped');
                this.handleRecordingStop(stream);
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event.error);
                this.showStatus('Recording error: ' + event.error, 'error');
                this.resetRecordingState();
            };

            this.mediaRecorder.start(1000);
            this.isRecording = true;

            this.updateMicButton();
            this.showRecordingStatus();
            this.startTimer();

            console.log('✅ Recording started successfully');

        } catch (error) {
            console.error('❌ Error starting recording:', error);
            let errorMessage = 'Could not access microphone. ';
            if (error.name === 'NotAllowedError') errorMessage += 'Please allow microphone access and try again.';
            else if (error.name === 'NotFoundError') errorMessage += 'No microphone found.';
            else errorMessage += error.message;

            this.showStatus(errorMessage, 'error');
            this.resetRecordingState();
        }
    }

    stopRecording() {
        console.log('⏹️ Stopping recording...');
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') this.mediaRecorder.stop();
        this.isRecording = false;
        this.updateMicButton();
        this.hideRecordingStatus();
        this.stopTimer();
    }

    handleRecordingStop(stream) {
        console.log('🎬 Handling recording stop...');
        stream.getTracks().forEach(track => track.stop());

        if (this.audioChunks.length === 0) {
            console.warn('⚠️ No audio chunks recorded');
            this.showStatus('No audio was recorded. Please try again.', 'error');
            this.resetRecordingState();
            return;
        }

        this.currentRecordingBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        console.log('📦 Created audio blob:', this.currentRecordingBlob.size, 'bytes');

        if (this.currentRecordingBlob.size === 0) {
            console.warn('⚠️ Empty audio blob');
            this.showStatus('Recording was empty. Please try again.', 'error');
            this.resetRecordingState();
            return;
        }

        this.showPlaybackSection();
        this.resetRecordingState();
        console.log('✅ Recording completed successfully');
    }

    showPlaybackSection() {
        const playbackSection = document.getElementById('playback-section');
        const audioElement = document.getElementById('recorded-audio');

        if (this.currentRecordingBlob) {
            const audioUrl = URL.createObjectURL(this.currentRecordingBlob);
            audioElement.src = audioUrl;
            playbackSection.classList.remove('hidden');
            console.log('🎵 Showing playback section');
        }
    }

    hidePlaybackSection() {
        const playbackSection = document.getElementById('playback-section');
        const audioElement = document.getElementById('recorded-audio');

        if (audioElement.src) {
            URL.revokeObjectURL(audioElement.src);
            audioElement.src = '';
        }

        playbackSection.classList.add('hidden');
        this.currentRecordingBlob = null;
        console.log('🚫 Hidden playback section');
    }

    updateMicButton() {
        const micBtn = document.getElementById('mic-btn');
        if (!micBtn) return;
        const micText = micBtn.querySelector('.mic-text');

        if (this.isRecording) {
            micBtn.classList.add('recording');
            if (micText) micText.textContent = 'Stop';
            micBtn.title = 'Click to stop recording';
        } else {
            micBtn.classList.remove('recording');
            if (micText) micText.textContent = 'Speak';
            micBtn.title = 'Click to start recording';
        }
    }

    showRecordingStatus() {
        const el = document.getElementById('recording-status');
        if (el) el.classList.remove('hidden');
    }

    hideRecordingStatus() {
        const el = document.getElementById('recording-status');
        if (el) el.classList.add('hidden');
    }

    startTimer() {
        const timerElement = document.querySelector('.recording-timer');
        this.recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            if (timerElement) timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    resetRecordingState() {
        this.isRecording = false;
        this.updateMicButton();
        this.hideRecordingStatus();
        this.stopTimer();
    }

    startNewRecording() {
        this.hidePlaybackSection();
        this.startRecording();
    }

    async transcribeRecording() {
        if (!this.currentRecordingBlob) {
            this.showStatus('No recording available to transcribe', 'error');
            return;
        }

        console.log('📝 Starting transcription...');

        try {
            this.showStatus('Transcribing your question...', 'loading');

            const formData = new FormData();
            formData.append('file', this.currentRecordingBlob, 'question.webm');

            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                body: formData
            });

            console.log('📡 Transcription response status:', response.status);

            if (!response.ok) {
                let errorMessage = `Transcription failed (${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (_) {}
                throw new Error(errorMessage);
            }

            const result = await response.json();

            if (result.success && result.text) {
                const q = document.getElementById('question-text');
                if (q) q.value = result.text;
                this.hidePlaybackSection();
                this.showStatus('✅ Question transcribed! You can edit it or ask directly.', 'success');
                console.log('✅ Transcription successful:', result.text);
            } else {
                throw new Error(result.error || 'Transcription failed');
            }

        } catch (error) {
            console.error('❌ Transcription error:', error);
            this.showStatus('Transcription failed: ' + error.message, 'error');
        }
    }

    // ===== Content processing =====
    async processContent() {
        // Defensive: find active tab, default to 'text'
        const activeBtn = document.querySelector('.tab-btn.active');
        const activeTab = activeBtn?.dataset?.tab || 'text';

        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
        }

        try {
            let requestData;
            let formData;
            let isFormData = false;

            if (activeTab === 'text') {
                const text = document.getElementById('text-input')?.value?.trim() || '';
                if (!text) throw new Error('Please enter some text to analyze');
                requestData = { type: 'text', text, summary_level: this.selectedSummaryLevel };

            } else if (activeTab === 'file') {
                const fileInput = document.getElementById('file-input');
                if (!fileInput?.files?.length) throw new Error('Please select a file to upload');

                formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('type', 'file');
                formData.append('summary_level', this.selectedSummaryLevel);
                isFormData = true;
            }

            const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
            this.showStatus(`Processing your content with ${levelNames[this.selectedSummaryLevel]} summary...`, 'loading');

            const response = await fetch('/api/process-content', {
                method: 'POST',
                ...(!isFormData && {
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify(requestData)
                }),
                ...(isFormData && { body: formData })
            });

            console.log('📡 Process content response status:', response.status);

            if (!response.ok) {
                const raw = await response.text();
                let msg = `Processing failed (${response.status})`;
                try {
                    const err = JSON.parse(raw);
                    msg = err.error || msg;
                } catch (_) {
                    msg = `${msg}: ${raw}`;
                }
                throw new Error(msg);
            }

            const result = await response.json();

            if (result.success) {
                this.showSummary(result.summary, result.audio_url, this.selectedSummaryLevel);
                this.showQASection();
                this.showStatus(`Content processed successfully with ${levelNames[this.selectedSummaryLevel]} summary! You can now ask questions.`, 'success');
                console.log('✅ Content processed successfully, QA stored:', result.qa_stored);

                // Give backend a moment if needed
                setTimeout(() => console.log('✅ Post-processing wait complete'), 1500);

            } else {
                throw new Error(result.error || 'Processing failed');
            }

        } catch (error) {
            console.error('❌ Process content error:', error);
            this.showStatus(error.message, 'error');
        } finally {
            if (processBtn) {
                processBtn.disabled = false;
                processBtn.innerHTML = '🚀 Analyze Content';
            }
        }
    }

    async askQuestion() {
        const questionText = document.getElementById('question-text')?.value?.trim() || '';
        const askBtn = document.getElementById('ask-btn');

        console.log('🔍 =========================');
        console.log('🔍 DEBUG: askQuestion called');
        console.log('🔍 Question text:', questionText);
        console.log('🔍 Question length:', questionText.length);
        console.log('🔍 =========================');

        if (!questionText) {
            this.showStatus('Please enter a question or record one using the microphone', 'error');
            return;
        }

        if (askBtn) {
            askBtn.disabled = true;
            askBtn.innerHTML = '<span class="loading-spinner"></span> Thinking...';
        }

        try {
            // (same logic as your original for QA readiness + ask flow)
            const response = await fetch('/api/ask-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ question: questionText })
            });

            if (!response.ok) {
                const txt = await response.text();
                let msg = `Request failed with status ${response.status}`;
                try {
                    const err = JSON.parse(txt);
                    msg = err.error || msg;
                } catch (_) {
                    msg = `Server error (${response.status}): ${txt}`;
                }
                throw new Error(msg);
            }

            const result = await response.json();
            if (result.success && result.answer) {
                this.showAnswer(result.answer, result.audio_url);
                const q = document.getElementById('question-text');
                if (q) q.value = '';
                this.showStatus('✅ Question answered successfully!', 'success');
            } else {
                throw new Error(result.error || 'No answer received');
            }

        } catch (error) {
            console.error('❌ COMPLETE ERROR DETAILS:', error);
            this.showStatus(`❌ ${error.message}`, 'error');
        } finally {
            if (askBtn) {
                askBtn.disabled = false;
                askBtn.innerHTML = 'Ask Question';
            }
            console.log('🔍 ========================= END DEBUG =========================');
        }
    }

    showSummary(summary, audioUrl, level) {
        const summarySection = document.getElementById('summary-section');
        const summaryText = document.getElementById('summary-text');
        const summaryAudio = document.getElementById('summary-audio');
        const levelBadge = document.getElementById('summary-level-indicator');

        if (summaryText) summaryText.textContent = summary;
        if (audioUrl && summaryAudio) summaryAudio.src = audioUrl;

        const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
        if (levelBadge) levelBadge.textContent = levelNames[level] || 'Standard';

        if (summarySection) summarySection.classList.remove('hidden');
    }

    showAnswer(answer, audioUrl) {
        const answerText = document.getElementById('answer-text');
        const answerAudio = document.getElementById('answer-audio');

        if (answerText) answerText.textContent = answer;
        if (audioUrl && answerAudio) answerAudio.src = audioUrl;

        const ans = document.getElementById('answer-section');
        if (ans) ans.scrollIntoView({ behavior: 'smooth' });
    }

    showQASection() {
        const el = document.getElementById('qa-section');
        if (el) el.classList.remove('hidden');
    }

    showStatus(message, type) {
        const statusEl = document.getElementById('status');
        if (!statusEl) return;
        statusEl.textContent = message;
        statusEl.className = `status ${type}`;
        statusEl.classList.remove('hidden');

        if (type !== 'loading') {
            setTimeout(() => statusEl.classList.add('hidden'), 5000);
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM loaded, initializing MyAIGist...');
    new MyAIGist();
});
