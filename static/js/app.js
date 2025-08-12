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
        this.selectedFiles = []; // For multi-file upload
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
                requestData = { type: 'text', text, summary_level: this.selectedSummaryLevel, voice: this.selectedVoice };

            } else if (activeTab === 'file') {
                const fileInput = document.getElementById('file-input');
                if (!fileInput?.files?.length) throw new Error('Please select a file to upload');

                formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('type', 'file');
                formData.append('summary_level', this.selectedSummaryLevel);
                formData.append('voice', this.selectedVoice);
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
                
                // Track summarization event
                this.trackEvent('content_summarized', {
                    content_type: activeTab,
                    summary_level: this.selectedSummaryLevel,
                    has_audio: !!result.audio_url
                });
                this.showQASection();
                this.showStatus(`Content processed successfully with ${levelNames[this.selectedSummaryLevel]} summary! You can now ask questions.`, 'success');
                console.log('✅ Content processed successfully, QA stored:', result.qa_stored);

                // Clear text input for next entry if it was a text submission
                const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
                if (activeTab === 'text') {
                    const textInput = document.getElementById('text-input');
                    if (textInput) {
                        textInput.value = '';
                        textInput.placeholder = 'Enter your next text here for AI analysis...';
                    }
                }

                // Refresh file shelf if document was stored for QA
                if (result.qa_stored) {
                    setTimeout(() => this.loadUserDocuments(), 1000);
                }

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
                    <button class="file-delete" onclick="myAIGist.deleteDocument('${doc.doc_id}')" title="Delete document">
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

    // Multi-File Upload Setup
    setupMultiFileUpload() {
        const multiFileInput = document.getElementById('multi-file-input');
        const selectedFilesDiv = document.getElementById('selected-files');
        const selectedFilesList = document.getElementById('selected-files-list');
        const uploadBtn = document.getElementById('upload-multiple-btn');

        if (multiFileInput) {
            multiFileInput.addEventListener('change', (e) => {
                this.selectedFiles = Array.from(e.target.files);
                this.updateSelectedFilesList();
            });
        }

        if (uploadBtn) {
            uploadBtn.addEventListener('click', this.uploadMultipleFiles);
        }
    }

    updateSelectedFilesList() {
        const selectedFilesDiv = document.getElementById('selected-files');
        const selectedFilesList = document.getElementById('selected-files-list');
        const uploadBtn = document.getElementById('upload-multiple-btn');

        if (!selectedFilesDiv || !selectedFilesList || !uploadBtn) return;

        if (this.selectedFiles.length === 0) {
            selectedFilesDiv.style.display = 'none';
            uploadBtn.disabled = true;
            return;
        }

        selectedFilesDiv.style.display = 'block';
        uploadBtn.disabled = false;

        selectedFilesList.innerHTML = this.selectedFiles.map((file, index) => `
            <div class="selected-file-item">
                <span class="selected-file-name">${file.name}</span>
                <button class="remove-file" onclick="myAIGist.removeSelectedFile(${index})" title="Remove file">
                    ×
                </button>
            </div>
        `).join('');

        // Update button text
        uploadBtn.textContent = `🚀 Upload ${this.selectedFiles.length} File${this.selectedFiles.length > 1 ? 's' : ''}`;
    }

    removeSelectedFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateSelectedFilesList();
        
        // Update the file input
        const multiFileInput = document.getElementById('multi-file-input');
        if (multiFileInput && this.selectedFiles.length === 0) {
            multiFileInput.value = '';
        }
    }

    async uploadMultipleFiles() {
        if (this.selectedFiles.length === 0) {
            this.showStatus('Please select files first', 'error');
            return;
        }

        if (this.selectedFiles.length > 5) {
            this.showStatus('Maximum 5 files allowed', 'error');
            return;
        }

        try {
            this.showStatus(`Uploading ${this.selectedFiles.length} files...`, 'loading');

            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            formData.append('summary_level', this.selectedSummaryLevel);
            formData.append('voice', this.selectedVoice);

            const response = await fetch('/api/upload-multiple-files', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showStatus(`Successfully uploaded ${data.successful_uploads} files!`, 'success');
                
                // Clear selected files
                this.selectedFiles = [];
                this.updateSelectedFilesList();
                document.getElementById('multi-file-input').value = '';

                // Display results
                this.displayMultiFileResults(data);
                
                // Refresh file shelf
                await this.loadUserDocuments();

                // Track successful multi-upload
                this.trackEvent('multi_file_upload', {
                    total_files: data.total_files,
                    successful_uploads: data.successful_uploads,
                    summary_level: this.selectedSummaryLevel
                });

            } else {
                throw new Error(data.error || 'Upload failed');
            }

        } catch (error) {
            console.error('❌ Multi-file upload error:', error);
            this.showStatus(`Upload error: ${error.message}`, 'error');
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
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM loaded, initializing MyAIGist...');
    window.myAIGist = new MyAIGist();
});
