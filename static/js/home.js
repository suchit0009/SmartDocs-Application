// DOM Elements
const modal = document.getElementById('uploadModal');
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseFilesBtn = document.getElementById('browseFilesBtn');
const fileList = document.getElementById('fileList');
const uploadForm = document.getElementById('uploadForm');
const loadingOverlay = document.getElementById('loadingOverlay');

// Modal Functions
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

// Loading Functions
function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// File Handling
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
    Array.from(fileInput.files).forEach((file, i) => {
        if (i !== index) dataTransfer.items.add(file);
    });
    fileInput.files = dataTransfer.files;
    updateSelectedFilesDisplay(fileInput.files);
}

// Event Listeners
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
    fileInput.files = e.dataTransfer.files;
    updateSelectedFilesDisplay(fileInput.files);
});

fileInput.addEventListener('change', () => {
    updateSelectedFilesDisplay(fileInput.files);
});

browseFilesBtn.addEventListener('click', () => fileInput.click());

window.onclick = (event) => {
    if (event.target === modal) closeUploadModal();
};

// Document Management
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

function appendDocumentToGrid(doc) {
    const grid = document.querySelector('#documents .document-grid');
    const card = document.createElement('div');
    card.className = 'document-card';
    card.onclick = () => viewDocument(doc.id);
    card.innerHTML = `<i class="fas fa-file"></i><p>${doc.title}</p>`;
    grid.insertBefore(card, grid.firstChild);
}

function appendDocumentToTable(doc) {
    const tbody = document.querySelector('#documents .table-container tbody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="action-buttons">
            <form method="POST" action="" onclick="event.stopPropagation();">
                <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                <input type="hidden" name="delete_document" value="true">
                <input type="hidden" name="doc_id" value="${doc.id}">
                <button type="submit" class="delete-btn" title="Delete"><i class="fas fa-trash-alt"></i></button>
            </form>
            <a href="/documents/edit/${doc.id}/" class="edit-btn" title="Edit" onclick="event.stopPropagation();"><i class="fas fa-pen"></i></a>
        </td>
        <td onclick="viewDocument('${doc.id}')">${doc.title}</td>
        <td onclick="viewDocument('${doc.id}')">${doc.file_type || 'Unknown'}</td>
        <td onclick="viewDocument('${doc.id}')">${formatFileSize(doc.file_size)}</td>
        <td onclick="viewDocument('${doc.id}')">${doc.category}</td>
        <td onclick="viewDocument('${doc.id}')"><span class="badge">Review</span></td>
        <td onclick="viewDocument('${doc.id}')">${doc.uploaded_at}</td>
    `;
    tbody.insertBefore(row, tbody.firstChild);
}

// Upload Form Submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(uploadForm);
    closeUploadModal();
    showLoading();

    try {
        const response = await fetch(uploadForm.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
        });
        const data = await response.json();
        hideLoading();

        const messagesContainer = document.getElementById('uploadMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.status}-message`;
        messageDiv.innerHTML = `${data.message}<button class="message-close" onclick="this.parentElement.remove()">×</button>`;
        messagesContainer.appendChild(messageDiv);

        if (data.status === 'success' && data.document) {
            appendDocumentToGrid(data.document);
            appendDocumentToTable(data.document);
            const docCountElement = document.querySelector('.nav-item[data-section="documents"] .document-count');
            if (docCountElement) docCountElement.textContent = parseInt(docCountElement.textContent) + 1;
        }
    } catch (error) {
        hideLoading();
        const messagesContainer = document.getElementById('uploadMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message error-message';
        messageDiv.innerHTML = `An error occurred: ${error.message}<button class="message-close" onclick="this.parentElement.remove()">×</button>`;
        messagesContainer.appendChild(messageDiv);
    }
});

// Navigation and Actions
function selectSection(navItem) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    navItem.classList.add('active');
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.getElementById(navItem.dataset.section).classList.add('active');
}

function logout() {
    window.location.href = '/logout/';
}

function viewDocument(docId) {
    window.location.href = `/documents/view/${docId}`;
}

function changePassword() {
    window.location.href = '/accounts/change-password/';
}

function updateProfile() {
    window.location.href = '/accounts/profile/';
}

function toggleNotifications() {
    alert('Notification toggle functionality to be implemented.');
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    const defaultNavItem = document.querySelector('.nav-item[data-section="documents"]');
    if (defaultNavItem) selectSection(defaultNavItem);
});