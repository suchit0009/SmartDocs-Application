let scale = 1;
const MIN_SCALE = 0.5;
const MAX_SCALE = 3;
const SCALE_STEP = 0.1;

// Use the homeUrl defined in the HTML
function goBack() {
    window.location.href = homeUrl; // Use the variable from the HTML
}

function switchTab(tabElement, tabId) {
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    tabElement.classList.add('active');
}

function fetchDocumentData(docId) {
    $.ajax({
        url: `/documents/document/${docId}/data/`,
        type: 'GET',
        success: function(response) {
            Object.keys(response).forEach(key => {
                const fieldId = key.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
                const textValue = response[key].text || response[key];
                const field = document.getElementById(fieldId);
                if (field) {
                    field.value = textValue || '';
                }
            });
        },
        error: function(xhr) {
            console.error("Error fetching document data:", xhr.responseText);
        }
    });
}

function saveDocumentData(docId) {
    let updatedData = {};
    document.querySelectorAll('#extracted-data .field-input').forEach(input => {
        const key = input.id.replace(/-/g, ' ');
        updatedData[key] = { text: input.value };
    });

    $.ajax({
        url: `/documents/document/${docId}/update/`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(updatedData),
        headers: { 'X-CSRFToken': getCsrfToken() },
        success: function() {
            alert('Document data saved successfully!');
        },
        error: function(xhr) {
            console.error("Error saving document data:", xhr.responseText);
            alert('Failed to save document data.');
        }
    });
}

function downloadDocument(docId) {
    window.location.href = `/documents/download/${docId}/`;
}

function zoomIn() {
    if (scale < MAX_SCALE) {
        scale += SCALE_STEP;
        updateZoom();
    }
}

function zoomOut() {
    if (scale > MIN_SCALE) {
        scale -= SCALE_STEP;
        updateZoom();
    }
}

function updateZoom() {
    const viewer = document.querySelector('.document-content img, .document-content embed, .document-content iframe');
    if (viewer) {
        viewer.style.transform = `scale(${scale})`;
    }
}

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return decodeURIComponent(value);
    }
    return null;
}

// Chat AI functionality (only for invoices, checked via JavaScript)
// Use documentCategory from the HTML instead of querying the DOM
if (documentCategory.toLowerCase() === 'invoice') {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    function setQuestion(question) {
        if (chatInput) {
            chatInput.value = question;
            sendMessage();
        }
    }

    function sendMessage() {
        if (!chatInput || !chatMessages) return;

        const question = chatInput.value.trim();
        if (!question) return;

        const userMessage = document.createElement('div');
        userMessage.classList.add('message', 'message-user');
        userMessage.textContent = question;
        chatMessages.appendChild(userMessage);

        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        typingIndicator.innerHTML = 'AI is typing<span>.</span><span>.</span><span>.</span>';
        chatMessages.appendChild(typingIndicator);

        typingIndicator.classList.add('active');
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        $.ajax({
            url: `/documents/document/${docId}/ask/`,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ question: question }),
            headers: { 'X-CSRFToken': getCsrfToken() },
            success: function(response) {
                typingIndicator.remove();
                const aiMessage = document.createElement('div');
                aiMessage.classList.add('message', 'message-ai');
                aiMessage.textContent = response.answer;
                chatMessages.appendChild(aiMessage);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            },
            error: function(xhr) {
                typingIndicator.remove();
                const aiMessage = document.createElement('div');
                aiMessage.classList.add('message', 'message-ai');
                aiMessage.textContent = "Sorry, I couldn't process your question.";
                chatMessages.appendChild(aiMessage);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });
    }

    if (sendBtn && chatInput) {
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Add debugging to confirm the script is running and variables are defined
    console.log("document_details.js loaded");
    console.log("docId:", docId);
    console.log("homeUrl:", homeUrl);
    console.log("documentCategory:", documentCategory);

    fetchDocumentData(docId);

    document.getElementById('downloadButton').addEventListener('click', (e) => {
        e.preventDefault();
        downloadDocument(docId);
    });

    document.getElementById('saveButton')?.addEventListener('click', () => saveDocumentData(docId));
    document.getElementById('zoomIn').addEventListener('click', zoomIn);
    document.getElementById('zoomOut').addEventListener('click', zoomOut);

    const shareModal = document.getElementById('shareModal');
    const closeModal = document.getElementById('closeModal');
    const cancelShare = document.getElementById('cancelShare');
    const confirmShare = document.getElementById('confirmShare');
    const userSearch = document.getElementById('userSearch');
    const userList = document.getElementById('userList');
    const selectedCountEl = document.getElementById('selectedCount');
    let selectedCount = 0;

    function showModal() {
        selectedCount = 0;
        selectedCountEl.textContent = '0';
        shareModal.style.display = 'flex';
        fetchUsers();
    }

    function hideModal() {
        shareModal.style.display = 'none';
    }

    document.querySelectorAll('.share-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            showModal();
        });
    });

    closeModal.addEventListener('click', hideModal);
    cancelShare.addEventListener('click', hideModal);

    const permissionOptions = document.querySelectorAll('.permission-option');
    permissionOptions.forEach(option => {
        option.addEventListener('click', function() {
            permissionOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    if (permissionOptions[0]) {
        permissionOptions[0].classList.add('selected');
    }

    userSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const userItems = userList.querySelectorAll('.user-item');
        userItems.forEach(item => {
            const userName = item.querySelector('.user-name').textContent.toLowerCase();
            const userEmail = item.querySelector('.user-email').textContent.toLowerCase();
            item.style.display = (userName.includes(searchTerm) || userEmail.includes(searchTerm)) ? 'flex' : 'none';
        });
    });

    confirmShare.addEventListener('click', function() {
        const selectedUsers = [];
        const userCheckboxes = document.querySelectorAll('.user-checkbox:checked');
        userCheckboxes.forEach(checkbox => {
            selectedUsers.push(checkbox.getAttribute('data-user-id'));
        });

        const selectedPermission = document.querySelector('.permission-option.selected');
        const permissionLevel = selectedPermission ? selectedPermission.getAttribute('data-permission') : null;

        if (selectedUsers.length === 0) {
            alert('Please select at least one user to share with.');
            return;
        }
        if (!permissionLevel) {
            alert('Please select a permission level.');
            return;
        }

        $.ajax({
            url: `/sharing/api/share/${docId}/`,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                users: selectedUsers,
                permission: permissionLevel
            }),
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            success: function(response) {
                alert(`Document successfully shared with ${selectedUsers.length} users!`);
                hideModal();
            },
            error: function(xhr) {
                console.error("Share error:", xhr.responseText);
                alert('Failed to share document. Please try again.');
            }
        });
    });

    function fetchUsers() {
        $.ajax({
            url: '/api/users/',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                userList.innerHTML = '';
                data.forEach(user => {
                    const avatarHTML = user.profile_picture 
                        ? `<img src="${user.profile_picture}" alt="${user.username}" class="profile-img" />`
                        : '<i class="fas fa-user"></i>';

                    const userItem = `
                        <div class="user-item">
                            <input type="checkbox" class="user-checkbox" data-user-id="${user.id}">
                            <div class="user-avatar">
                                ${avatarHTML}
                            </div>
                            <div class="user-info">
                                <div class="user-name">${user.username}</div>
                                <div class="user-email">${user.email}</div>
                            </div>
                        </div>
                    `;
                    userList.insertAdjacentHTML('beforeend', userItem);
                });
                attachUserCheckboxListeners();
            },
            error: function(error) {
                console.error('Error fetching users:', error);
                showSampleUsers();
            }
        });
    }

    function showSampleUsers() {
        userList.innerHTML = '';
        const sampleUsers = [
            { id: 1, username: 'John Doe', email: 'john@example.com' },
            { id: 2, username: 'Jane Smith', email: 'jane@example.com' },
            { id: 3, username: 'Robert Johnson', email: 'robert@example.com' }
        ];
        sampleUsers.forEach(user => {
            const userItem = `
                <div class="user-item">
                    <input type="checkbox" class="user-checkbox" data-user-id="${user.id}">
                    <div class="user-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                        <div class="user-email">${user.email}</div>
                    </div>
                </div>
            `;
            userList.insertAdjacentHTML('beforeend', userItem);
        });
        attachUserCheckboxListeners();
    }

    function attachUserCheckboxListeners() {
        const userCheckboxes = document.querySelectorAll('.user-checkbox');
        userCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                selectedCount += this.checked ? 1 : -1;
                selectedCountEl.textContent = selectedCount;
                const selectionCount = document.getElementById('selectionCount');
                if (selectedCount > 0) {
                    selectionCount.classList.add('active');
                } else {
                    selectionCount.classList.remove('active');
                }
            });
        });
    }
});