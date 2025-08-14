class MyAIGist {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordingTimer = null;
        this.startTime = null;
        this.currentRecordingBlob = null;
        this.selectedSummaryLevel = 'standard'; // Default to standard
        this.selectedVoice = 'nova'; // Default voice
        this.selectedInputs = []; // Unified input system (text and files)
        this.userDocuments = []; // Track user's uploaded documents

        // Bind methods (extra safety against "not a function" if something rebinds context)
        this.processContent = this.processContent.bind(this);
        this.askQuestion = this.askQuestion.bind(this);
        this.uploadMultipleFiles = this.uploadMultipleFiles.bind(this);
        this.deleteDocument = this.deleteDocument.bind(this);

        this.init();
    }

    init() {
        console.log('🚀 Initializing MyAIGist...');
        this.setupEventListeners();
        this.setupTabs();
        this.setupSummaryLevels();
        this.setupVoiceSelection();
        this.setupFileShelf();
        this.setupMultiFileUpload();
        this.loadUserDocuments();

        // Debug: list methods to ensure processContent exists
        const protoMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(this));
        console.log('🧩 Methods on instance:', protoMethods);
    }

    // Google Analytics event tracking helper
    trackEvent(eventName, parameters = {}) {
        if (typeof window.gtag === 'function') {
            window.gtag('event', eventName, parameters);
            console.log('📊 GA Event tracked:', eventName, parameters);
        }
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

        // ✅ Unified input system handling
        const addTextBtn = document.getElementById('add-text-btn');
        if (addTextBtn) {
            addTextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showTextInputModal();
            });
        }

        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(Array.from(e.target.files));
                e.target.value = ''; // Reset input for re-selection
            });
        }

        // Summary action buttons
        const copySummaryBtn = document.getElementById('copy-summary-btn');
        if (copySummaryBtn) {
            copySummaryBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.copySummaryToClipboard();
            });
        }

        const emailSummaryBtn = document.getElementById('email-summary-btn');
        if (emailSummaryBtn) {
            emailSummaryBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.emailSummary();
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

    setupVoiceSelection() {
        const voiceSelect = document.getElementById('voice-select');
        if (voiceSelect) {
            voiceSelect.addEventListener('change', () => {
                this.selectedVoice = voiceSelect.value;
                console.log('🔊 Voice selected:', this.selectedVoice);
            });
        }
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
        // Check if we have inputs
        if (!this.selectedInputs?.length) {
            this.showStatus('❌ Please add some content to analyze', 'error');
            return;
        }

        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
        }

        try {
            // Separate text and file inputs
            const textInputs = this.selectedInputs.filter(input => input.type === 'text');
            const fileInputs = this.selectedInputs.filter(input => input.type === 'file');

            // If we have multiple inputs or any files, use multi-input processing
            if (this.selectedInputs.length > 1 || fileInputs.length > 0) {
                return this.processMultipleInputs();
            }

            // Single text input - use simple text processing
            if (textInputs.length === 1) {
                const requestData = {
                    type: 'text', 
                    text: textInputs[0].content,
                    summary_level: this.selectedSummaryLevel,
                    voice: this.selectedVoice
                };
                
                return this.processSingleContent(requestData, false);
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

    async processSingleContent(requestData, isFormData) {
        const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
        this.showStatus(`Processing your content with ${levelNames[this.selectedSummaryLevel]} summary...`, 'loading');

        const response = await fetch('/api/process-content', {
            method: 'POST',
            ...(!isFormData && {
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(requestData)
            }),
            ...(isFormData && { body: requestData })
        });

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
            // Phase 1: Show summary immediately
            this.showSummary(result.summary, null, this.selectedSummaryLevel);
            this.showQASection();
            this.showStatus(`Content processed successfully! You can now ask questions.`, 'success');
            
            // Phase 2: Generate audio in background
            if (result.summary && result.summary.trim().length > 10) {
                setTimeout(async () => {
                    try {
                        const audioLoading = document.getElementById('audio-loading');
                        if (audioLoading) audioLoading.classList.remove('hidden');
                        await this.generateAudioInBackground(result.summary, this.selectedVoice);
                    } catch (audioError) {
                        console.error('❌ Audio generation failed:', audioError);
                        const audioLoading = document.getElementById('audio-loading');
                        if (audioLoading) {
                            audioLoading.classList.add('hidden');
                            audioLoading.style.display = 'none';
                        }
                    }
                }, 1000);
            }

            // Clear inputs and refresh
            this.clearAllInputs();
            if (result.qa_stored) {
                setTimeout(() => this.loadUserDocuments(), 1000);
            }
        } else {
            throw new Error(result.error || 'Processing failed');
        }
    }

    async processMultipleInputs() {
        // Use the existing multi-file upload logic but adapted for mixed inputs
        console.log('📁 Processing multiple inputs...');
        
        const formData = new FormData();
        const textInputs = this.selectedInputs.filter(input => input.type === 'text');
        const fileInputs = this.selectedInputs.filter(input => input.type === 'file');
        
        // Add files
        fileInputs.forEach((input, index) => {
            formData.append('files', input.file);
        });
        
        // Add text entries as "virtual files"
        textInputs.forEach((input, index) => {
            const textBlob = new Blob([input.content], { type: 'text/plain' });
            const textFile = new File([textBlob], `${input.title}.txt`, { type: 'text/plain' });
            formData.append('files', textFile);
        });
        
        formData.append('summary_level', this.selectedSummaryLevel);
        formData.append('voice', this.selectedVoice);
        
        const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
        this.showStatus(`Processing ${this.selectedInputs.length} input(s) with ${levelNames[this.selectedSummaryLevel]} summary...`, 'loading');

        const response = await fetch('/api/upload-multiple-files', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const raw = await response.text();
            let msg = `Multi-input processing failed (${response.status})`;
            try {
                const err = JSON.parse(raw);
                msg = err.error || msg;
            } catch (_) {
                msg = `${msg}: ${raw}`;
            }
            throw new Error(msg);
        }

        const data = await response.json();
        console.log('✅ Multi-input response:', data);

        if (data.success) {
            // Phase 1: Show summary immediately
            const summaryText = data.combined_summary || 'Content processed successfully';
            this.showSummary(summaryText, null, this.selectedSummaryLevel);
            this.showQASection();
            await this.loadUserDocuments();

            // Track event
            this.trackEvent('multi_input_processed', {
                total_inputs: this.selectedInputs.length,
                text_inputs: textInputs.length,
                file_inputs: fileInputs.length,
                summary_level: this.selectedSummaryLevel
            });
            
            this.showStatus(`Successfully analyzed ${this.selectedInputs.length} input(s)!`, 'success');
            
            // Phase 2: Generate audio in background
            if (summaryText && summaryText.trim().length > 10) {
                setTimeout(async () => {
                    try {
                        const audioLoading = document.getElementById('audio-loading');
                        if (audioLoading) audioLoading.classList.remove('hidden');
                        await this.generateAudioInBackground(summaryText, data.voice || this.selectedVoice);
                    } catch (audioError) {
                        console.error('❌ Audio generation failed:', audioError);
                        const audioLoading = document.getElementById('audio-loading');
                        if (audioLoading) {
                            audioLoading.classList.add('hidden');
                            audioLoading.style.display = 'none';
                        }
                    }
                }, 1000);
            }
            
            // Clear inputs
            this.clearAllInputs();
        } else {
            throw new Error(data.error || 'Multi-input processing failed');
        }
    }

    clearAllInputs() {
        this.selectedInputs = [];
        this.updateInputDisplay();
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
                body: JSON.stringify({ question: questionText, voice: this.selectedVoice })
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
                
                // Track question asking event
                this.trackEvent('question_asked', {
                    question_length: questionText.length,
                    has_audio_response: !!result.audio_url
                });
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
        const audioLoading = document.getElementById('audio-loading');
        const levelBadge = document.getElementById('summary-level-indicator');

        if (summaryText) summaryText.textContent = summary;
        
        // Handle audio URL - show/hide audio element based on availability
        if (summaryAudio) {
            if (audioUrl) {
                summaryAudio.src = audioUrl;
                summaryAudio.style.display = 'block';
            } else {
                summaryAudio.style.display = 'none';
            }
        }
        
        // Hide audio loading indicator when audio URL is provided
        if (audioLoading) {
            if (audioUrl) {
                audioLoading.classList.add('hidden');
            } else {
                audioLoading.classList.add('hidden'); // Initially hidden, will be shown when audio generation starts
            }
        }

        const levelNames = { quick: 'Quick', standard: 'Standard', detailed: 'Detailed' };
        if (levelBadge) levelBadge.textContent = levelNames[level] || 'Standard';

        // Show action buttons when summary is available
        const summaryActions = document.getElementById('summary-actions');
        if (summaryActions && summary && summary.trim()) {
            summaryActions.classList.remove('hidden');
        }

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

    // File Shelf Management
    setupFileShelf() {
        const shelfToggle = document.getElementById('shelf-toggle');
        const fileShelf = document.getElementById('file-shelf');
        
        if (shelfToggle && fileShelf) {
            shelfToggle.addEventListener('click', () => {
                fileShelf.classList.toggle('minimized');
                shelfToggle.textContent = fileShelf.classList.contains('minimized') ? '▶' : '◀';
            });
        }
    }

    async loadUserDocuments() {
        try {
            const response = await fetch('/api/user-documents');
            const data = await response.json();
            
            if (data.documents) {
                this.userDocuments = data.documents;
                this.updateFileShelf();
            }
        } catch (error) {
            console.error('❌ Error loading user documents:', error);
        }
    }

    updateFileShelf() {
        const fileList = document.getElementById('file-list');
        const fileCountBadge = document.getElementById('file-count-badge');
        
        if (!fileList || !fileCountBadge) return;

        fileCountBadge.textContent = this.userDocuments.length;

        if (this.userDocuments.length === 0) {
            fileList.innerHTML = '<li class="no-files-message">No documents uploaded yet</li>';
            return;
        }

        fileList.innerHTML = this.userDocuments.map(doc => {
            // Determine document type and icon
            const isTextEntry = doc.title.startsWith('Text Entry');
            const docIcon = isTextEntry ? '📝' : '📄';
            const docType = isTextEntry ? 'Text' : 'File';
            
            // Format date nicely
            const uploadDate = new Date(doc.upload_time);
            const formattedDate = uploadDate.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <li class="file-item" data-doc-id="${doc.doc_id}">
                    <div class="file-info">
                        <div class="file-name">
                            ${docIcon} ${doc.title}
                        </div>
                        <div class="file-meta">
                            ${docType} • ${formattedDate} • ${doc.chunk_count} chunks
                        </div>
                    </div>
                    <button class="file-delete" onclick="window.myAIGist.deleteDocument('${doc.doc_id}')" title="Delete document">
                        ×
                    </button>
                </li>
            `;
        }).join('');
    }

    async deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            this.showStatus('Deleting document...', 'loading');
            
            const response = await fetch('/api/delete-document', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doc_id: docId })
            });

            const data = await response.json();

            if (data.success) {
                this.showStatus('Document deleted successfully!', 'success');
                // Remove from local array
                this.userDocuments = this.userDocuments.filter(doc => doc.doc_id !== docId);
                this.updateFileShelf();
                
                // Track deletion event
                this.trackEvent('document_deleted', {
                    doc_id: docId,
                    chunks_removed: data.chunks_removed
                });
            } else {
                throw new Error(data.error || 'Failed to delete document');
            }
        } catch (error) {
            console.error('❌ Delete document error:', error);
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    // File Upload Setup (unified for single or multiple files)
    setupMultiFileUpload() {
        // The file input change handler is now in setupEventListeners()
        // This method is kept for compatibility but doesn't need to do anything
        console.log('✅ File upload system initialized (unified single/multi)');
    }

    // Old methods removed - using unified input system

    async uploadMultipleFiles() {
        try {
            console.log('🚀 Starting multi-file upload...');
            console.log('📁 Selected files:', this.selectedFiles.map(f => f.name));

            if (this.selectedFiles.length === 0) {
                this.showStatus('Please select files first', 'error');
                return false; // Return false to indicate failure
            }

            if (this.selectedFiles.length > 5) {
                this.showStatus('Maximum 5 files allowed', 'error');
                return false;
            }

            // Validate file sizes and types
            for (const file of this.selectedFiles) {
                if (file.size > 50 * 1024 * 1024) { // 50MB limit
                    this.showStatus(`File "${file.name}" is too large (max 50MB)`, 'error');
                    return false;
                }
                
                const allowedTypes = ['.pdf', '.docx', '.txt'];
                const hasValidExtension = allowedTypes.some(ext => 
                    file.name.toLowerCase().endsWith(ext)
                );
                
                if (!hasValidExtension) {
                    this.showStatus(`File "${file.name}" has unsupported format. Allowed: PDF, DOCX, TXT`, 'error');
                    return false;
                }
            }

            this.showStatus(`Processing ${this.selectedFiles.length} document${this.selectedFiles.length > 1 ? 's' : ''}...`, 'loading');

            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                console.log(`📄 Adding file: ${file.name} (${file.size} bytes)`);
                formData.append('files', file);
            });
            formData.append('summary_level', this.selectedSummaryLevel);
            formData.append('voice', this.selectedVoice);

            console.log('📡 Sending multi-file analysis request...');
            
            const response = await fetch('/api/upload-multiple-files', {
                method: 'POST',
                body: formData
            });

            console.log('📡 Response status:', response.status);

            if (!response.ok) {
                let errorDetails = `HTTP ${response.status} ${response.statusText}`;
                
                // Handle specific error types
                if (response.status === 504) {
                    errorDetails = 'Analysis timed out. The files may be too large or the server is busy. Please try with fewer or smaller files.';
                } else if (response.status >= 500) {
                    errorDetails = 'Server error occurred. Please try again in a moment.';
                } else {
                    // Try to get more detailed error info for 4xx errors
                    try {
                        const errorText = await response.text();
                        
                        // Only try JSON parsing if the response looks like JSON
                        if (errorText.trim().startsWith('{') || errorText.trim().startsWith('[')) {
                            try {
                                const errorData = JSON.parse(errorText);
                                errorDetails = errorData.error || errorData.message || errorDetails;
                            } catch (parseError) {
                                console.warn('⚠️ Could not parse error response as JSON, using raw text');
                                // Use a clean excerpt of the HTML error if it's HTML
                                if (errorText.includes('<title>') && errorText.includes('</title>')) {
                                    const titleMatch = errorText.match(/<title>(.*?)<\/title>/);
                                    errorDetails = titleMatch ? titleMatch[1] : errorDetails;
                                } else {
                                    errorDetails = errorText.substring(0, 200) + (errorText.length > 200 ? '...' : '');
                                }
                            }
                        } else if (errorText.includes('<title>') && errorText.includes('</title>')) {
                            // Extract title from HTML error pages
                            const titleMatch = errorText.match(/<title>(.*?)<\/title>/);
                            errorDetails = titleMatch ? titleMatch[1] : errorDetails;
                        } else {
                            // Use a clean excerpt for other response types
                            errorDetails = errorText.substring(0, 200) + (errorText.length > 200 ? '...' : '');
                        }
                    } catch (readError) {
                        console.warn('⚠️ Could not read error response:', readError.message);
                        // Keep the default HTTP status message
                    }
                }
                
                console.error('❌ Upload failed:', errorDetails);
                throw new Error(errorDetails);
            }

            const data = await response.json();
            console.log('✅ Upload response:', data);

            if (data.success) {
                // Phase 1: Show summary immediately for responsive feel
                const summaryText = data.combined_summary || 'Multiple files processed successfully';
                this.showSummary(summaryText, null, this.selectedSummaryLevel); // No audio yet
                
                // Clear selected files
                this.selectedFiles = [];
                this.updateFileDisplay();
                const fileInput = document.getElementById('file-input');
                if (fileInput) fileInput.value = '';

                // Show Q&A section
                this.showQASection();
                
                // Refresh file shelf
                await this.loadUserDocuments();

                // Track successful multi-upload
                this.trackEvent('multi_file_upload', {
                    total_files: data.total_files,
                    successful_uploads: data.successful_uploads,
                    summary_level: this.selectedSummaryLevel
                });
                
                this.showStatus(`Successfully analyzed ${data.successful_uploads} document${data.successful_uploads > 1 ? 's' : ''}!`, 'success');
                
                // Phase 2: Generate audio in background (if there's text to convert)
                console.log('🎵 Checking audio generation conditions:');
                console.log('  - summaryText:', summaryText ? `"${summaryText.substring(0, 100)}..."` : 'null/undefined');
                console.log('  - summaryText length:', summaryText ? summaryText.length : 0);
                console.log('  - voice:', data.voice || this.selectedVoice);
                
                // Always try to generate audio if we have valid summary text
                if (summaryText && summaryText.trim().length > 10) { // Changed condition - just check for meaningful text
                    console.log('✅ Conditions met, calling generateAudioInBackground');
                    setTimeout(async () => {
                        try {
                            // Show audio loading indicator
                            const audioLoading = document.getElementById('audio-loading');
                            if (audioLoading) {
                                audioLoading.classList.remove('hidden');
                            }
                            
                            await this.generateAudioInBackground(summaryText, data.voice || this.selectedVoice);
                        } catch (audioError) {
                            console.error('❌ Audio generation failed with error:', audioError);
                            // Hide loading indicator on error
                            const audioLoading = document.getElementById('audio-loading');
                            if (audioLoading) {
                                audioLoading.classList.add('hidden');
                                audioLoading.style.display = 'none';
                                console.log('❌ Audio loading indicator hidden due to error');
                            }
                        }
                    }, 1000); // Add small delay to ensure UI is ready
                } else {
                    console.log('❌ Audio generation skipped - no meaningful text');
                    console.log('  - summaryText value:', JSON.stringify(summaryText));
                    console.log('  - summaryText type:', typeof summaryText);
                    console.log('  - summaryText length:', summaryText ? summaryText.length : 0);
                }
                
                return true; // Return true to indicate success

            } else {
                throw new Error(data.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('❌ Multi-file upload error:', error);
            this.showStatus(`Analysis error: ${error.message}`, 'error');
            return false; // Return false to indicate failure
        }
    }

    async generateAudioInBackground(text, voice) {
        // Generate audio for text in the background and update UI when ready
        try {
            console.log('🎵 Generating audio in background...');
            
            // Update status to show audio is being generated
            const currentStatus = document.getElementById('status');
            const originalStatus = currentStatus ? currentStatus.textContent : '';
            this.showStatus('Generating audio...', 'loading');
            
            const response = await fetch('/api/generate-audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice })
            });

            if (response.ok) {
                const audioData = await response.json();
                if (audioData.success && audioData.audio_url) {
                    // Update the summary section with audio
                    const summaryAudio = document.getElementById('summary-audio');
                    const audioLoading = document.getElementById('audio-loading');
                    
                    if (summaryAudio) {
                        summaryAudio.src = audioData.audio_url;
                        summaryAudio.style.display = 'block';
                        console.log('✅ Audio generated and added to summary');
                    }
                    
                    // Hide the audio loading indicator
                    if (audioLoading) {
                        audioLoading.classList.add('hidden');
                        audioLoading.style.display = 'none';
                        console.log('✅ Audio loading indicator hidden');
                    }
                }
            } else {
                console.warn('⚠️ Audio generation failed, continuing without audio');
                // Hide loading indicator on failure
                const audioLoading = document.getElementById('audio-loading');
                if (audioLoading) {
                    audioLoading.classList.add('hidden');
                    audioLoading.style.display = 'none';
                    console.log('⚠️ Audio loading indicator hidden due to generation failure');
                }
            }
            
            // Restore original status or clear loading status
            if (originalStatus && !originalStatus.includes('loading')) {
                this.showStatus(originalStatus, 'success');
            } else {
                // Hide status after a short delay if it was just the loading message
                setTimeout(() => {
                    if (currentStatus) currentStatus.classList.add('hidden');
                }, 2000);
            }
            
        } catch (error) {
            console.warn('⚠️ Background audio generation failed:', error.message);
            // Hide loading indicator on error
            const audioLoading = document.getElementById('audio-loading');
            if (audioLoading) {
                audioLoading.classList.add('hidden');
                audioLoading.style.display = 'none';
                console.log('❌ Audio loading indicator hidden due to background generation error');
            }
            // Don't show error to user since audio is optional
        }
    }

    displayMultiFileResults(data) {
        // Show the summary section
        const summarySection = document.getElementById('summary-section');
        const summaryContent = document.getElementById('summary-content');
        const summaryLevelIndicator = document.getElementById('summary-level-indicator');

        if (summarySection && summaryContent && summaryLevelIndicator) {
            summarySection.classList.remove('hidden');
            summaryLevelIndicator.textContent = this.selectedSummaryLevel.charAt(0).toUpperCase() + 
                                              this.selectedSummaryLevel.slice(1);

            // Display combined summary or individual results
            if (data.combined_summary) {
                summaryContent.textContent = data.combined_summary;
            } else {
                // Display individual results
                const resultsText = data.results
                    .filter(r => r.success)
                    .map(r => `📄 ${r.filename}:\n${r.summary}`)
                    .join('\n\n---\n\n');
                summaryContent.textContent = resultsText || 'Upload completed but no summaries generated.';
            }

            // Handle audio if available
            if (data.audio_url) {
                this.handleAudioResponse(data.audio_url);
            }

            // Show failed uploads if any
            const failedUploads = data.results.filter(r => !r.success);
            if (failedUploads.length > 0) {
                const errorMsg = `Some files failed to upload:\n${failedUploads.map(f => `• ${f.filename}: ${f.error}`).join('\n')}`;
                this.showStatus(errorMsg, 'error');
            }
        }

        // Enable Q&A section
        const qaSection = document.getElementById('qa-section');
        if (qaSection) {
            qaSection.classList.remove('hidden');
        }
    }

    // Copy summary to clipboard
    async copySummaryToClipboard() {
        const summaryText = document.getElementById('summary-text');
        if (!summaryText || !summaryText.textContent) {
            this.showStatus('No summary available to copy', 'error');
            return;
        }

        const textToCopy = summaryText.textContent;
        let copySuccess = false;

        try {
            // Try modern clipboard API first (requires HTTPS)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(textToCopy);
                copySuccess = true;
            } else {
                // Fallback for HTTP environments
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                textArea.style.position = 'fixed';
                textArea.style.left = '-9999px';
                textArea.style.top = '-9999px';
                document.body.appendChild(textArea);
                
                textArea.focus();
                textArea.select();
                
                try {
                    copySuccess = document.execCommand('copy');
                } catch (fallbackErr) {
                    console.error('Fallback copy failed:', fallbackErr);
                }
                
                document.body.removeChild(textArea);
            }

            if (copySuccess) {
                this.showStatus('✅ Summary copied to clipboard!', 'success');
                
                // Track event for analytics
                this.trackEvent('summary_copied', {
                    content_length: textToCopy.length,
                    summary_level: this.selectedSummaryLevel
                });
                
                // Visual feedback on button
                const copyBtn = document.getElementById('copy-summary-btn');
                if (copyBtn) {
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = '✅ Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                    }, 2000);
                }
            } else {
                throw new Error('Copy operation failed');
            }
        } catch (err) {
            console.error('Failed to copy to clipboard:', err);
            this.showStatus('❌ Failed to copy to clipboard. Please select and copy the text manually.', 'error');
        }
    }

    // Email summary
    emailSummary() {
        const summaryText = document.getElementById('summary-text');
        if (!summaryText || !summaryText.textContent) {
            this.showStatus('No summary available to email', 'error');
            return;
        }

        try {
            const subject = 'MyAIGist Summary: ';
            const body = summaryText.textContent;
            const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
            
            // Open default email client
            window.location.href = mailtoLink;
            
            // Track event for analytics
            this.trackEvent('summary_emailed', {
                content_length: body.length,
                summary_level: this.selectedSummaryLevel
            });
            
            this.showStatus('✅ Opening email client...', 'success');
        } catch (err) {
            console.error('Failed to open email client:', err);
            this.showStatus('❌ Failed to open email client', 'error');
        }
    }

    // Unified Input System Methods
    showTextInputModal() {
        if (this.selectedInputs.length >= 5) {
            this.showStatus('❌ Maximum 5 inputs allowed', 'error');
            return;
        }

        // Create modal HTML
        const modal = document.createElement('div');
        modal.className = 'text-input-modal';
        modal.innerHTML = `
            <div class="text-input-modal-content">
                <h3>✍️ Add Text Entry</h3>
                <textarea 
                    id="modal-text-input" 
                    placeholder="Enter your text here for AI analysis..."
                    maxlength="10000"
                ></textarea>
                <div class="text-input-modal-actions">
                    <button class="text-input-modal-btn cancel">Cancel</button>
                    <button class="text-input-modal-btn add">Add Text</button>
                </div>
            </div>
        `;

        // Add to body
        document.body.appendChild(modal);

        // Focus textarea
        const textarea = modal.querySelector('#modal-text-input');
        setTimeout(() => textarea.focus(), 100);

        // Handle buttons
        const cancelBtn = modal.querySelector('.cancel');
        const addBtn = modal.querySelector('.add');

        cancelBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        addBtn.addEventListener('click', () => {
            const text = textarea.value.trim();
            if (!text) {
                this.showStatus('❌ Please enter some text', 'error');
                // Close modal after showing error
                setTimeout(() => {
                    if (document.body.contains(modal)) {
                        document.body.removeChild(modal);
                    }
                }, 2000);
                return;
            }
            if (text.length < 10) {
                this.showStatus('❌ Text must be at least 10 characters', 'error');
                // Close modal after showing error
                setTimeout(() => {
                    if (document.body.contains(modal)) {
                        document.body.removeChild(modal);
                    }
                }, 2000);
                return;
            }

            this.addTextInput(text);
            document.body.removeChild(modal);
        });

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    addTextInput(text) {
        const textInput = {
            id: `text_${Date.now()}`,
            type: 'text',
            content: text,
            title: `Text Entry ${this.selectedInputs.filter(i => i.type === 'text').length + 1}`,
            preview: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
            size: text.length
        };

        this.selectedInputs.push(textInput);
        this.updateInputDisplay();
        this.showStatus('✅ Text entry added!', 'success');
    }

    handleFileSelection(files) {
        if (files.length === 0) return;

        const remainingSlots = 5 - this.selectedInputs.length;
        if (files.length > remainingSlots) {
            this.showStatus(`❌ Can only add ${remainingSlots} more item(s). Maximum 5 inputs allowed.`, 'error');
            return;
        }

        files.forEach(file => {
            const fileInput = {
                id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                type: 'file',
                file: file,
                title: file.name,
                preview: `${file.type || 'Unknown type'} • ${this.formatFileSize(file.size)}`,
                size: file.size
            };

            this.selectedInputs.push(fileInput);
        });

        this.updateInputDisplay();
        this.showStatus(`✅ Added ${files.length} file(s)!`, 'success');
    }

    removeInput(inputId) {
        this.selectedInputs = this.selectedInputs.filter(input => input.id !== inputId);
        this.updateInputDisplay();
        this.showStatus('✅ Input removed', 'success');
    }

    updateInputDisplay() {
        const inputsList = document.getElementById('selected-inputs-list');
        const inputsContainer = document.getElementById('selected-inputs');
        const addTextBtn = document.getElementById('add-text-btn');
        const fileInputLabel = document.querySelector('.file-input-label');

        if (!inputsList) return;

        // Update button states
        const isMaxReached = this.selectedInputs.length >= 5;
        if (addTextBtn) {
            addTextBtn.disabled = isMaxReached;
            addTextBtn.title = isMaxReached ? 'Maximum 5 inputs reached' : 'Add text entry';
        }
        if (fileInputLabel) {
            if (isMaxReached) {
                fileInputLabel.style.opacity = '0.5';
                fileInputLabel.style.cursor = 'not-allowed';
                fileInputLabel.title = 'Maximum 5 inputs reached';
            } else {
                fileInputLabel.style.opacity = '1';
                fileInputLabel.style.cursor = 'pointer';
                fileInputLabel.title = 'Add document(s)';
            }
        }

        // Show/hide container and warning
        if (this.selectedInputs.length === 0) {
            inputsContainer.style.display = 'none';
            this.removeWarning();
        } else {
            inputsContainer.style.display = 'block';
            
            inputsList.innerHTML = this.selectedInputs.map(input => `
                <div class="input-item" data-id="${input.id}">
                    <div class="input-item-icon">
                        ${input.type === 'text' ? '📝' : '📄'}
                    </div>
                    <div class="input-item-content">
                        <div class="input-item-header">
                            <h4 class="input-item-title">${this.escapeHtml(input.title)}</h4>
                            <span class="input-item-type">${input.type.toUpperCase()}</span>
                        </div>
                        <p class="input-item-preview">${this.escapeHtml(input.preview)}</p>
                        ${input.type === 'text' ? 
                            `<div class="input-item-meta">${input.size} characters</div>` :
                            `<div class="input-item-meta">${this.formatFileSize(input.size)}</div>`
                        }
                    </div>
                    <button class="input-item-remove" onclick="window.myAIGist.removeInput('${input.id}')" title="Remove">×</button>
                </div>
            `).join('');

            // Show warning when approaching limit
            if (this.selectedInputs.length >= 4) {
                this.showWarning();
            } else {
                this.removeWarning();
            }
        }
    }

    showWarning() {
        const existingWarning = document.querySelector('.input-limit-warning');
        const inputsContainer = document.getElementById('selected-inputs');
        
        if (existingWarning) {
            // Update existing warning with current count
            existingWarning.textContent = `${5 - this.selectedInputs.length} input slot(s) remaining`;
            return;
        }

        const warning = document.createElement('div');
        warning.className = 'input-limit-warning';
        warning.textContent = `${5 - this.selectedInputs.length} input slot(s) remaining`;
        
        inputsContainer.appendChild(warning);
    }

    removeWarning() {
        const warning = document.querySelector('.input-limit-warning');
        if (warning) warning.remove();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM loaded, initializing MyAIGist...');
    window.myAIGist = new MyAIGist();
});
