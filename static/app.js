class FileProcessor {
    constructor() {
        this.fileInput = document.querySelector('input[type="file"]');
        this.processButton = document.querySelector('button');
        this.progressBar = document.querySelector('progress');
        this.logArea = document.querySelector('pre');
        this.downloadSection = document.querySelector('#download-section');
        this.currentProcessId = null;
        this.processedMessages = new Set();
        
        this.processButton.addEventListener('click', () => this.processFiles());
        this.downloadSection.style.display = 'none';
    }
    
    log(message) {
        this.logArea.textContent += `${message}\n`;
        this.logArea.scrollTop = this.logArea.scrollHeight;
    }
    
    updateProgress(progress, currentFile, totalFiles) {
        const progressBar = document.querySelector('progress');
        const percentageDisplay = document.querySelector('.progress-percentage');
        const filesDisplay = document.querySelector('.progress-files');
        
        progressBar.value = progress;
        percentageDisplay.textContent = `${Math.round(progress)}%`;
        
        if (currentFile && totalFiles) {
            filesDisplay.textContent = `Processed: ${currentFile} / ${totalFiles} files`;
        }
    }
    
    async processFiles() {
        const file = this.fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }
        
        // Clear previous state
        this.logArea.textContent = '';
        this.updateProgress(0);
        this.processButton.disabled = true;
        this.downloadSection.style.display = 'none';
        this.processedMessages.clear();
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            this.currentProcessId = data.process_id;
            this.startStatusPolling(data.process_id);
            
        } catch (error) {
            this.log(`Error: ${error.message}`);
            this.processButton.disabled = false;
        }
    }
    
    async startStatusPolling(processId) {
        const pollStatus = async () => {
            try {
                const response = await fetch(`/api/status/${processId}`);
                const data = await response.json();
                
                if (data.status === 'error') {
                    throw new Error(data.message);
                }
                
                this.updateProgress(data.progress, data.current_file, data.total_files);
                
                // Display new messages
                if (data.messages) {
                    for (const message of data.messages) {
                        if (!this.processedMessages.has(message)) {
                            this.log(message);
                            this.processedMessages.add(message);
                        }
                    }
                }
                
                if (data.progress === 100) {
                    this.processButton.disabled = false;
                    this.downloadSection.style.display = 'block';
                    return;
                }
                
                // Continue polling
                setTimeout(pollStatus, 1000);
                
            } catch (error) {
                this.log(`Error: ${error.message}`);
                this.processButton.disabled = false;
            }
        };
        
        pollStatus();
    }
    
    async downloadFile() {
        if (!this.currentProcessId) return;
        window.location.href = `/api/download/${this.currentProcessId}`;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.processor = new FileProcessor();
}); 