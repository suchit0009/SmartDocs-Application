document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const shareModal = document.getElementById('shareModal');
    const closeModal = document.getElementById('closeModal');
    const cancelShare = document.getElementById('cancelShare');
    const confirmShare = document.getElementById('confirmShare');
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    const permissionOptions = document.querySelectorAll('.permission-option');
    const userSearch = document.getElementById('userSearch');
    const userList = document.getElementById('userList');
    const selectionCount = document.getElementById('selectionCount');
    const selectedCountEl = document.getElementById('selectedCount');
    
    // Initialize selected users count
    let selectedCount = 0;
    
    // Event Listeners for closing modal
    closeModal.addEventListener('click', hideModal);
    cancelShare.addEventListener('click', hideModal);
    
    // Hide modal function
    function hideModal() {
        shareModal.style.display = 'none';
    }
    
    // Show modal function - called when share button is clicked
    function showModal() {
        // Show the modal
        document.getElementById('shareModal').style.display = 'flex';
        // Fetch and populate user data when the modal is opened
        fetchUsers();
    }

    
    // Toggle user selection
    userCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            selectedCount += this.checked ? 1 : -1;
            selectedCountEl.textContent = selectedCount;
            // Optionally, you can toggle an "active" class on the selection count banner here
        });
    });
    
    // Toggle permission selection
    permissionOptions.forEach(option => {
        option.addEventListener('click', function() {
            permissionOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    // Search functionality for user list
    userSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const userItems = userList.querySelectorAll('.user-item');
        userItems.forEach(item => {
            const userName = item.querySelector('.user-name').textContent.toLowerCase();
            const userEmail = item.querySelector('.user-email').textContent.toLowerCase();
            item.style.display = (userName.includes(searchTerm) || userEmail.includes(searchTerm)) ? 'flex' : 'none';
        });
    });
    
    // Handle share confirmation
    confirmShare.addEventListener('click', function() {
        const selectedUsers = [];
        userCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selectedUsers.push(checkbox.getAttribute('data-user-id'));
            }
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
        
        const shareData = {
            users: selectedUsers,
            permission: permissionLevel,
            documentId: getCurrentDocumentId() // Replace with actual logic
        };
        
        console.log('Share data:', shareData);
        alert(`Document shared with ${selectedUsers.length} users with ${permissionLevel} permission`);
        hideModal();
    });
    
    // Helper function to get current document ID (example placeholder)
    function getCurrentDocumentId() {
        return 'doc-123';
    }
    
    // Set default permission option
    permissionOptions[0].classList.add('selected');
    
    // Attach the showModal function to the share button(s)
    window.addEventListener('load', function() {
        const shareButtons = document.querySelectorAll('.btn-primary');
        shareButtons.forEach(button => {
            if (button.innerHTML.includes('fa-share-alt')) {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    showModal();
                });
            }
        });
    });
});

function fetchUsers() {
    $.ajax({
        url: '/api/users/', // Ensure this URL matches your Django URL pattern
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            var userList = $('#userList');
            userList.empty(); // Clear any existing user items

            // Iterate over each user returned from the API
            $.each(data, function(index, user) {
                // Use an image if a profile picture exists; otherwise, show the icon
                var avatarHTML = user.profile_picture 
                    ? '<img src="' + user.profile_picture + '" alt="' + user.username + '" class="profile-img" />'
                    : '<i class="fas fa-user"></i>';

                // Construct the HTML for a single user item
                var userItem = `
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
                userList.append(userItem);
            });

            // Reattach event listeners to new checkboxes (if needed)
            attachUserCheckboxListeners();
        },
        error: function(error) {
            console.error('Error fetching users:', error);
        }
    });
}

// Function to attach checkbox event listeners (if you need to update selection count, etc.)
function attachUserCheckboxListeners() {
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    userCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Update your selected count or perform any other logic here.
        });
    });
}