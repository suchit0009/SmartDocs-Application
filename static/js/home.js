// Global mappings for categories and sections
const sectionCategoryMap = {
    'License': 'license',
    'Passport': 'passport',
    'Invoice': 'invoices',
    'Check': 'checks',
    'Resume': 'resume'
};

const categoryFromSection = {
    'license': 'License',
    'passport': 'Passport',
    'invoices': 'Invoice',
    'checks': 'Check',
    'resume': 'Resume'
};

const modal = document.getElementById('uploadModal');
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseFilesBtn = document.getElementById('browseFilesBtn');
const fileList = document.getElementById('fileList');
const uploadForm = document.getElementById('uploadForm');
const loadingOverlay = document.getElementById('loadingOverlay');

function openUploadModal() {
    document.body.classList.add('modal-open');
    modal.style.display = 'flex';
}

function closeUploadModal() {
    document.body.classList.remove('modal-open');
    modal.style.display = 'none';
    fileInput.value = '';
    fileList.innerHTML = '';
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function updateSelectedFilesDisplay(files) {
    fileList.innerHTML = '';
    Array.from(files).forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.classList.add('file-item');
        fileItem.innerHTML = `
            <span>${file.name}</span>
            <button class="cancel-btn" onclick="removeFile(${index})">X</button>
        `;
        fileList.appendChild(fileItem);
    });
}

function removeFile(index) {
    const dataTransfer = new DataTransfer();
    const files = fileInput.files;
    Array.from(files).forEach((file, i) => {
        if (i !== index) dataTransfer.items.add(file);
    });
    fileInput.files = dataTransfer.files;
    updateSelectedFilesDisplay(fileInput.files);
}

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const dataTransfer = new DataTransfer();
        Array.from(files).forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
        updateSelectedFilesDisplay(fileInput.files);
    }
});

fileInput.addEventListener('change', () => {
    updateSelectedFilesDisplay(fileInput.files);
});

browseFilesBtn.addEventListener('click', () => {
    fileInput.click();
});

window.onclick = function(event) {
    if (event.target === modal) closeUploadModal();
};

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function normalizeCategory(category) {
    if (!category) {
        console.warn('Category is null or undefined, defaulting to "Document"');
        return 'Document';
    }
    const categoryMap = {
        'license': 'License',
        'check': 'Check',
        'invoice': 'Invoice',
        'passport': 'Passport',
        'resume': 'Resume'
    };
    const normalized = categoryMap[category.toLowerCase()] || category;
    console.log(`Normalizing category: Input=${category}, Output=${normalized}`);
    return normalized;
}

// Document Management Functions
function appendDocumentToGrid(doc, sectionId) {
    console.log(`Attempting to append document ${doc.id} to grid in section ${sectionId}`);
    const grid = document.querySelector(`#${sectionId} .document-grid`);
    if (!grid) {
        console.error(`Grid not found for section ${sectionId}. DOM elements:`, document.querySelectorAll(`#${sectionId}`));
        return;
    }

    const docCategory = normalizeCategory(doc.category);
    console.log(`Document category: ${docCategory}, Section category: ${categoryFromSection[sectionId]}`);
    if (sectionId !== 'documents') {
        const sectionCategory = categoryFromSection[sectionId];
        if (docCategory.toLowerCase() !== sectionCategory.toLowerCase()) {
            console.log(`Skipping document ${doc.id} in section ${sectionId} due to category mismatch.`);
            return;
        }
    }

    const noDocsMessage = grid.querySelector('p');
    if (noDocsMessage && noDocsMessage.textContent.includes('No')) {
        console.log('Removing "No documents uploaded yet" message from grid');
        noDocsMessage.remove();
    }

    const card = document.createElement('div');
    card.className = 'document-card';
    card.setAttribute('data-doc-id', doc.id);
    card.setAttribute('onclick', `viewDocument('${doc.id}')`);

    let iconClass = 'fas fa-file';
    if (sectionId === 'license') iconClass = 'fas fa-id-card';
    else if (sectionId === 'passport') iconClass = 'fas fa-passport';
    else if (sectionId === 'invoices') iconClass = 'fas fa-file-invoice';
    else if (sectionId === 'checks') iconClass = 'fas fa-money-check-alt';
    else if (sectionId === 'resume') iconClass = 'fas fa-file-alt';

    const displayTitle = doc.title || 'Untitled Document';
    card.innerHTML = `
        <i class="${iconClass}"></i>
        <p>${displayTitle}</p>
    `;
    grid.insertBefore(card, grid.firstChild);
    console.log(`Successfully added document card ${doc.id} to grid in section ${sectionId}`);
    // Verify the element is in the DOM
    console.log(`Grid contents after append:`, grid.innerHTML);
}

function appendDocumentToTable(doc, sectionId) {
    console.log(`Attempting to append document ${doc.id} to table in section ${sectionId}`);
    const tbody = document.querySelector(`#${sectionId} .table-container tbody`);
    if (!tbody) {
        console.error(`Table body not found for section ${sectionId}. DOM elements:`, document.querySelectorAll(`#${sectionId}`));
        return;
    }

    const docCategory = normalizeCategory(doc.category);
    console.log(`Document category: ${docCategory}, Section category: ${categoryFromSection[sectionId]}`);
    if (sectionId !== 'documents') {
        const sectionCategory = categoryFromSection[sectionId];
        if (docCategory.toLowerCase() !== sectionCategory.toLowerCase()) {
            console.log(`Skipping document ${doc.id} in section ${sectionId} due to category mismatch.`);
            return;
        }
    }

    const noDocsRow = tbody.querySelector('tr td[colspan="7"]');
    if (noDocsRow && noDocsRow.textContent.includes('No')) {
        console.log('Removing "No documents uploaded yet" message from table');
        noDocsRow.parentElement.remove();
    }

    const displayTitle = doc.title || 'Untitled Document';
    const row = document.createElement('tr');
    row.setAttribute('data-doc-id', doc.id);
    row.setAttribute('data-category', docCategory);
    row.innerHTML = `
        <td class="action-buttons">
            <button class="delete-btn" title="Delete" data-doc-id="${doc.id}" data-doc-title="${displayTitle}" data-doc-category="${docCategory}" onclick="event.stopPropagation(); showDeleteModal('${doc.id}', '${displayTitle}', '${docCategory}')">
                <i class="fas fa-trash-alt"></i>
            </button>
            <a href="/documents/edit/${doc.id}/" class="edit-btn" title="Edit" onclick="event.stopPropagation();">
                <i class="fas fa-pen"></i>
            </a>
        </td>
        <td onclick="viewDocument('${doc.id}')">${displayTitle}</td>
        <td onclick="viewDocument('${doc.id}')">${doc.file_type || 'Unknown'}</td>
        <td onclick="viewDocument('${doc.id}')">${formatFileSize(doc.file_size)}</td>
        <td onclick="viewDocument('${doc.id}')">${docCategory}</td>
        <td onclick="viewDocument('${doc.id}')"><span class="badge badge-${doc.status?.toLowerCase() || 'review'}">${doc.status || 'Review'}</span></td>
        <td onclick="viewDocument('${doc.id}')">${doc.uploaded_at}</td>
    `;
    row.style.animation = 'rowFadeIn 0.5s ease-in-out';
    tbody.insertBefore(row, tbody.firstChild);
    console.log(`Successfully added document row ${doc.id} to table in section ${sectionId}`);
    // Verify the element is in the DOM
    console.log(`Table body contents after append:`, tbody.innerHTML);
}


function removeDocumentFromGrid(docId, sectionId) {
    const selector = `#${sectionId} .document-card[data-doc-id="${docId}"]`;
    const elements = document.querySelectorAll(selector);
    console.log(`Removing ${elements.length} grid elements for docId ${docId} in section ${sectionId}`);
    elements.forEach(element => element.remove());

    const grid = document.querySelector(`#${sectionId} .document-grid`);
    if (grid && !grid.querySelector('.document-card')) {
        grid.innerHTML = `<p>No ${sectionId === 'documents' ? 'documents' : sectionId} uploaded yet.</p>`;
    }
}

function removeDocumentFromTable(docId, sectionId) {
    const selector = `#${sectionId} tr[data-doc-id="${docId}"]`;
    const elements = document.querySelectorAll(selector);
    console.log(`Removing ${elements.length} table rows for docId ${docId} in section ${sectionId}`);
    elements.forEach(element => element.remove());

    const tbody = document.querySelector(`#${sectionId} tbody`);
    if (tbody && !tbody.querySelector('tr')) {
        tbody.innerHTML = `<tr><td colspan="7">No ${sectionId === 'documents' ? 'documents' : sectionId} uploaded yet.</td></tr>`;
    }
}

function showToast(message, type = 'info') {
    const messagesContainer = document.getElementById('uploadMessages');
    if (!messagesContainer) {
        console.error('uploadMessages container not found in DOM');
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.innerHTML = `
        ${message}
        <button class="message-close" onclick="this.parentElement.remove()">×</button>
    `;
    messagesContainer.appendChild(messageDiv);
    setTimeout(() => messageDiv.remove(), 3000); // Remove after 3 seconds
}


function updateDocumentCount(sectionId, increment) {
    console.log(`Updating document count for section: ${sectionId}, increment: ${increment}`);
    const docCountElement = document.querySelector(`.nav-item[data-section="${sectionId}"] .document-count`);
    if (docCountElement) {
        const currentCount = parseInt(docCountElement.textContent) || 0;
        const newCount = Math.max(currentCount + increment, 0);
        docCountElement.textContent = newCount;
        console.log(`Updated count for ${sectionId}: ${newCount}`);
    } else {
        console.error(`Document count element not found for section: ${sectionId}`);
    }
}

// Upload Handling
uploadForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(uploadForm);

    closeUploadModal();
    showLoading();

    fetch(uploadForm.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        const messagesContainer = document.getElementById('uploadMessages');
        if (!messagesContainer) {
            console.error('uploadMessages container not found in DOM');
        } else {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.status}-message`;
            messageDiv.innerHTML = `
                ${data.message}
                <button class="message-close" onclick="this.parentElement.remove()">×</button>
            `;
            messagesContainer.appendChild(messageDiv);

            setTimeout(() => {
                messageDiv.remove();
            }, 3000);
        }

        if (data.status === 'success' && data.document) {
            console.log('Upload successful, document:', data.document);

            // Normalize the category
            const normalizedCategory = normalizeCategory(data.document.category);
            data.document.category = normalizedCategory;

            // Append to the general "documents" section
            appendDocumentToGrid(data.document, 'documents');
            appendDocumentToTable(data.document, 'documents');
            updateDocumentCount('documents', 1);

            // Append to the category-specific section (if applicable)
            const sectionId = sectionCategoryMap[normalizedCategory];
            if (sectionId) {
                appendDocumentToGrid(data.document, sectionId);
                appendDocumentToTable(data.document, sectionId);
                updateDocumentCount(sectionId, 1);
            } else {
                console.warn(`No section found for category: ${normalizedCategory}`);
            }
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Upload error:', error);
        showToast(`An error occurred: ${error.message}`, 'error');
    });
});

// Section Selection
function selectSection(navItem) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    navItem.classList.add('active');
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    const sectionId = navItem.getAttribute('data-section');
    document.getElementById(sectionId).classList.add('active');
}

// Delete Functionality
let currentDocId = null;
let currentDocCategory = null;

function showDeleteModal(docId, docTitle, category) {
    currentDocId = docId;
    currentDocCategory = category;
    const modal = document.getElementById('deleteModal');
    const titleElement = document.getElementById('deleteModalTitle');
    const messageElement = document.getElementById('deleteModalMessage');
    const deleteBtn = document.getElementById('confirmDeleteBtn');

    showLoading();

    fetch(`/documents/check-shared-status/${docId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');

        if (data.is_shared) {
            titleElement.textContent = 'Delete Shared Document?';
            titleElement.className = 'shared';
            messageElement.textContent = `The document "${docTitle}" is shared with ${data.shared_with_count} user(s): ${data.shared_with_usernames}. Deleting it will remove access for everyone. Are you sure?`;
            messageElement.className = 'shared';
            deleteBtn.className = 'btn-delete';
        } else {
            titleElement.textContent = 'Delete Document?';
            titleElement.className = 'not-shared';
            messageElement.textContent = `Are you sure you want to delete "${docTitle}"? This action cannot be undone.`;
            messageElement.className = 'not-shared';
            deleteBtn.className = 'btn-delete not-shared';
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error checking shared status:', error);
        showToast('Error checking document status', 'error');
    });
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    document.body.classList.remove('modal-open');
    currentDocId = null;
    currentDocCategory = null;
}

function confirmDelete() {
    if (!currentDocId) return;

    showLoading();

    const formData = new FormData();
    formData.append('delete_document', 'true');
    formData.append('doc_id', currentDocId);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch('', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Deletion failed');
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') throw new Error(data.message || 'Deletion failed');

        // Update UI after successful deletion
        const normalizedCategory = normalizeCategory(currentDocCategory);
        const sectionId = sectionCategoryMap[normalizedCategory];
        const sectionsToUpdate = ['documents'];
        if (sectionId) {
            sectionsToUpdate.push(sectionId);
        }

        sectionsToUpdate.forEach(section => {
            removeDocumentFromGrid(currentDocId, section);
            removeDocumentFromTable(currentDocId, section);
            updateDocumentCount(section, -1);
        });

        showToast('Document deleted successfully', 'success');
    })
    .catch(error => {
        console.error('Deletion error:', error);
        showToast(error.message || 'Failed to delete document', 'error');
    })
    .finally(() => {
        hideLoading();
        closeDeleteModal();
    });
}

// Event Listeners
document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function(event) {
        event.stopPropagation();
        const docId = this.getAttribute('data-doc-id');
        const docTitle = this.getAttribute('data-doc-title');
        const docCategory = this.getAttribute('data-doc-category');
        showDeleteModal(docId, docTitle, docCategory);
    });
});

function logout() {
    console.log("Logout function called");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const logoutUrl = document.querySelector('#logout-url').value;

    if (!csrfToken) {
        console.error('CSRF token not found!');
        return;
    }

    if (!logoutUrl) {
        console.error('Logout URL not found!');
        return;
    }

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = logoutUrl; // Use the resolved URL (e.g., '/logout/')

    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;

    form.appendChild(csrfInput);
    document.body.appendChild(form);
    console.log("Form action:", form.action); // Debug the URL
    form.submit();
}

function viewDocument(docId) {
    window.location.href = `/documents/view/${docId}`;
}

function changePassword() {
    window.location.href = "/accounts/change-password/";
}

function updateProfile() {
    window.location.href = "/accounts/profile/";
}

function toggleNotifications() {
    alert("Notification toggle functionality to be implemented.");
}

// Message close functionality
        document.addEventListener('DOMContentLoaded', function() {
            const messagesContainer = document.getElementById('messages-container');
            
            if (messagesContainer) {
                // Auto dismiss after 3 seconds
                setTimeout(function() {
                    removeMessages();
                }, 3000);
                
                // Handle close button clicks
                const closeButtons = document.querySelectorAll('.message-close');
                closeButtons.forEach(button => {
                    button.addEventListener('click', function(e) {
                        e.preventDefault();
                        const message = this.parentElement;
                        message.classList.add('fade-out');
                        setTimeout(() => {
                            message.remove();
                            if (messagesContainer.children.length === 0) {
                                removeMessages();
                            }
                        }, 300);
                    });
                });
            }
            
            function removeMessages() {
                if (messagesContainer) {
                    messagesContainer.classList.add('fade-out');
                    setTimeout(() => {
                        messagesContainer.remove();
                    }, 300);
                }
            }
        });
