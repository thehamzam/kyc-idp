/**
 * Document Extraction App - JavaScript
 * Supports bulk document upload with individual processing
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const fileListItems = document.getElementById('file-list-items');
    const clearAllFilesBtn = document.getElementById('clear-all-files');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const errorMessage = document.getElementById('error-message');
    const resultImage = document.getElementById('result-image');
    const extractedData = document.getElementById('extracted-data');
    const uploadAnotherBtn = document.getElementById('upload-another');
    
    // History DOM Elements
    const historyEmpty = document.getElementById('history-empty');
    const historyTableContainer = document.getElementById('history-table-container');
    const historyTbody = document.getElementById('history-tbody');
    const detailsModal = document.getElementById('details-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const modalMeta = document.getElementById('modal-meta');
    const modalData = document.getElementById('modal-data');

    // Allowed file types and size limit
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    const maxFileSize = 10 * 1024 * 1024; // 10MB

    // Selected files state: array of { file: File, valid: boolean, error: string|null }
    let selectedFiles = [];

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addFiles(files);
        }
    });

    // File input change - handle multiple files
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            addFiles(e.target.files);
        }
    });

    // Clear all files button
    clearAllFilesBtn.addEventListener('click', () => {
        clearAllFiles();
    });

    // Form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await uploadFiles();
    });

    // Upload another button
    uploadAnotherBtn.addEventListener('click', () => {
        resetToUpload();
    });

    // Modal close button
    closeModalBtn.addEventListener('click', () => {
        detailsModal.style.display = 'none';
    });

    // Close modal on outside click
    detailsModal.addEventListener('click', (e) => {
        if (e.target === detailsModal) {
            detailsModal.style.display = 'none';
        }
    });

    // Load submission history on page load
    loadSubmissionHistory();


    /**
     * Validate a single file
     * @returns {{ valid: boolean, error: string|null }}
     */
    function validateFile(file) {
        if (!allowedTypes.includes(file.type)) {
            return { valid: false, error: 'Invalid file type. Must be JPEG, PNG, GIF, or WebP.' };
        }
        if (file.size > maxFileSize) {
            return { valid: false, error: 'File size exceeds 10MB limit.' };
        }
        return { valid: true, error: null };
    }

    /**
     * Add files to the selection
     */
    function addFiles(files) {
        hideError();
        
        for (const file of files) {
            // Check if file already exists in selection
            const exists = selectedFiles.some(sf => sf.file.name === file.name && sf.file.size === file.size);
            if (exists) continue;
            
            const validation = validateFile(file);
            selectedFiles.push({
                file: file,
                valid: validation.valid,
                error: validation.error
            });
        }
        
        renderFileList();
        updateUploadButton();
        
        // Reset file input so same files can be selected again
        fileInput.value = '';
    }

    /**
     * Remove a file from selection by index
     */
    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderFileList();
        updateUploadButton();
    }

    /**
     * Clear all selected files
     */
    function clearAllFiles() {
        selectedFiles = [];
        renderFileList();
        updateUploadButton();
        hideError();
    }

    /**
     * Get only valid files for upload
     */
    function getValidFiles() {
        return selectedFiles.filter(sf => sf.valid).map(sf => sf.file);
    }

    /**
     * Render the file list UI
     */
    function renderFileList() {
        if (selectedFiles.length === 0) {
            fileList.style.display = 'none';
            uploadArea.style.display = 'block';
            return;
        }

        fileList.style.display = 'block';
        uploadArea.style.display = 'none';

        fileListItems.innerHTML = selectedFiles.map((sf, index) => `
            <div class="file-item ${sf.valid ? '' : 'file-item-invalid'}">
                <span class="file-item-name">${escapeHtml(sf.file.name)}</span>
                ${sf.error ? `<span class="file-item-error">${escapeHtml(sf.error)}</span>` : ''}
                <button type="button" class="btn-remove-file" onclick="removeFileAtIndex(${index})">✕</button>
            </div>
        `).join('');
    }

    /**
     * Update upload button state
     */
    function updateUploadButton() {
        const validFiles = getValidFiles();
        uploadBtn.disabled = validFiles.length === 0;
        
        if (validFiles.length === 0 && selectedFiles.length > 0) {
            showError('No valid files selected. Please check file types and sizes.');
        }
    }

    // Expose removeFile to global scope for onclick handlers
    window.removeFileAtIndex = function(index) {
        removeFile(index);
    };

    /**
     * Upload files and get extraction results
     */
    async function uploadFiles() {
        const validFiles = getValidFiles();
        if (validFiles.length === 0) {
            showError('Please select at least one valid file.');
            return;
        }

        // Show loading state with progress
        uploadSection.style.display = 'none';
        loadingSection.style.display = 'flex';
        hideError();

        // Update loading message for bulk upload
        const loadingText = loadingSection.querySelector('p');
        loadingText.textContent = `Processing ${validFiles.length} document(s)...`;

        try {
            const formData = new FormData();
            validFiles.forEach(file => {
                formData.append('files[]', file);
            });

            const response = await fetch('/upload-bulk', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayBulkResults(result);
                loadSubmissionHistory();
            } else {
                showError(result.error || 'Upload failed. Please try again.');
                resetToUpload();
            }
        } catch (error) {
            console.error('Upload error:', error);
            showError('Failed to upload files. Please check your connection and try again.');
            resetToUpload();
        } finally {
            loadingSection.style.display = 'none';
        }
    }

    /**
     * Display bulk upload results
     */
    function displayBulkResults(result) {
        const { results, summary } = result;
        
        let html = `<div class="bulk-results-summary">
            <p><strong>Upload Complete:</strong> ${summary.succeeded} of ${summary.total} documents processed successfully.</p>
        </div>`;

        if (summary.failed > 0) {
            html += `<div class="bulk-results-errors">
                <p><strong>Failed documents:</strong></p>
                <ul>`;
            results.filter(r => !r.success).forEach(r => {
                html += `<li>${escapeHtml(r.filename)}: ${escapeHtml(r.error)}</li>`;
            });
            html += `</ul></div>`;
        }

        if (summary.succeeded > 0) {
            html += `<div class="bulk-results-success">
                <p><strong>Successfully processed:</strong></p>
                <ul>`;
            results.filter(r => r.success).forEach(r => {
                const name = r.data?.name || 'Unknown';
                html += `<li>${escapeHtml(r.filename)} - ${escapeHtml(name)}</li>`;
            });
            html += `</ul></div>`;
        }

        extractedData.innerHTML = html;
        resultImage.style.display = 'none';
        resultsSection.querySelector('.image-panel').style.display = 'none';
        resultsSection.style.display = 'block';
    }


    /**
     * Display single extraction results (kept for backward compatibility)
     */
    function displayResults(result) {
        resultImage.src = result.image_data;
        resultImage.style.display = 'block';
        resultsSection.querySelector('.image-panel').style.display = 'block';

        const data = result.data;
        let html = '<dl class="data-list">';

        const fieldLabels = {
            name: 'Full Name',
            date_of_birth: 'Date of Birth',
            document_number: 'Document Number',
            document_type: 'Document Type',
            expiry_date: 'Expiry Date',
            nationality: 'Nationality',
            address: 'Address',
            sex: 'Sex'
        };

        let hasData = false;
        for (const [key, label] of Object.entries(fieldLabels)) {
            if (data[key]) {
                html += `<dt>${label}</dt><dd>${escapeHtml(data[key])}</dd>`;
                hasData = true;
            }
        }

        if (data.additional_fields && Object.keys(data.additional_fields).length > 0) {
            for (const [key, value] of Object.entries(data.additional_fields)) {
                if (value) {
                    html += `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`;
                    hasData = true;
                }
            }
        }

        html += '</dl>';

        if (!hasData) {
            html = '<p class="no-data">No information could be extracted from this document.</p>';
        }

        extractedData.innerHTML = html;
        resultsSection.style.display = 'block';
    }

    /**
     * Reset to upload state
     */
    function resetToUpload() {
        clearAllFiles();
        resultsSection.style.display = 'none';
        uploadSection.style.display = 'block';
        resultImage.style.display = 'block';
        resultsSection.querySelector('.image-panel').style.display = 'block';
    }

    /**
     * Show error message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    /**
     * Hide error message
     */
    function hideError() {
        errorMessage.style.display = 'none';
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load submission history from server
     */
    async function loadSubmissionHistory() {
        try {
            const response = await fetch('/submissions');
            const result = await response.json();

            if (result.success) {
                displaySubmissionHistory(result.submissions);
            }
        } catch (error) {
            console.error('Failed to load submission history:', error);
        }
    }

    /**
     * Display submission history in table
     */
    function displaySubmissionHistory(submissions) {
        if (!submissions || submissions.length === 0) {
            historyEmpty.style.display = 'block';
            historyTableContainer.style.display = 'none';
            return;
        }

        historyEmpty.style.display = 'none';
        historyTableContainer.style.display = 'block';

        historyTbody.innerHTML = submissions.map(sub => `
            <tr data-id="${sub.id}">
                <td>${escapeHtml(sub.filename || '-')}</td>
                <td>${escapeHtml(sub.document_type || '-')}</td>
                <td>${escapeHtml(sub.name || '-')}</td>
                <td>${formatDate(sub.created_at)}</td>
                <td>
                    <button class="btn-view" onclick="event.stopPropagation(); viewSubmission(${sub.id})">View</button>
                    <button class="btn-delete" onclick="event.stopPropagation(); deleteSubmission(${sub.id})">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Format date for display
     */
    function formatDate(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    /**
     * View submission details
     */
    window.viewSubmission = async function(id) {
        try {
            const response = await fetch(`/submissions/${id}`);
            const result = await response.json();

            if (result.success) {
                displaySubmissionDetails(result.submission);
            } else {
                showError(result.error || 'Failed to load submission details.');
            }
        } catch (error) {
            console.error('Failed to load submission:', error);
            showError('Failed to load submission details.');
        }
    };

    /**
     * Display submission details in modal
     */
    function displaySubmissionDetails(submission) {
        modalMeta.innerHTML = `
            <p><strong>Filename:</strong> ${escapeHtml(submission.filename)}</p>
            <p><strong>Submitted:</strong> ${formatDate(submission.created_at)}</p>
        `;

        const modalImage = document.getElementById('modal-image');
        const modalImagePanel = document.getElementById('modal-image-panel');
        if (submission.image_data) {
            modalImage.src = submission.image_data;
            modalImagePanel.style.display = 'block';
        } else {
            modalImagePanel.style.display = 'none';
        }

        const data = submission.extraction_data || {};
        let html = '<h4>Extracted Information</h4><dl class="data-list">';

        const fieldLabels = {
            name: 'Full Name',
            date_of_birth: 'Date of Birth',
            document_number: 'Document Number',
            document_type: 'Document Type',
            expiry_date: 'Expiry Date',
            nationality: 'Nationality',
            address: 'Address',
            sex: 'Sex'
        };

        for (const [key, label] of Object.entries(fieldLabels)) {
            if (data[key]) {
                html += `<dt>${label}</dt><dd>${escapeHtml(data[key])}</dd>`;
            }
        }

        if (data.additional_fields && Object.keys(data.additional_fields).length > 0) {
            for (const [key, value] of Object.entries(data.additional_fields)) {
                if (value) {
                    html += `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`;
                }
            }
        }

        html += '</dl>';
        modalData.innerHTML = html;
        detailsModal.style.display = 'flex';
    }

    /**
     * Delete a submission
     */
    window.deleteSubmission = async function(id) {
        if (!confirm('Are you sure you want to delete this submission?')) {
            return;
        }

        try {
            const response = await fetch(`/submissions/${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();

            if (result.success) {
                loadSubmissionHistory();
            } else {
                showError(result.error || 'Failed to delete submission.');
            }
        } catch (error) {
            console.error('Failed to delete submission:', error);
            showError('Failed to delete submission.');
        }
    };
});
