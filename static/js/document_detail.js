// document_detail.js

// Navigate back to the document list
function goBack() {
    window.location.href = 'http://127.0.0.1:8000/home/';
  }
  
  // Switch between tabs
  function switchTab(tabElement, tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
    tabElement.classList.add('active');
  }
  
  // Fetch document data via AJAX
  function fetchDocumentData(docId) {
    $.ajax({
      url: `/documents/document/${docId}/data/`,
      type: 'GET',
      success: function(response) {
        console.log("Data received:", response);
        Object.keys(response).forEach(key => {
          const fieldId = key.replace(/ /g, '_');
          const textValue = response[key].text;
          const field = document.getElementById(fieldId);
          if (field) {
            field.value = textValue;
            console.log(`Updated field ${fieldId} with value: ${textValue}`);
          } else {
            console.warn(`Field with ID '${fieldId}' not found`);
          }
        });
      },
      error: function(xhr, status, error) {
        console.error("Error fetching document data:", error);
        console.error("Response:", xhr.responseText);
        // Optionally, call a fallback function:
        // populateLicenseData();
      }
    });
  }
  
  // Save updated document data via AJAX
  function saveDocumentData(docId) {
    const updatedData = {
      "driving license number": { "text": document.getElementById('driving_license_number').value },
      "name": { "text": document.getElementById('name').value },
      "date of birth": { "text": document.getElementById('date_of_birth').value },
      "citizenship no": { "text": document.getElementById('citizenship_no').value },
      "contact no": { "text": document.getElementById('contact_no').value },
      "date of issue": { "text": document.getElementById('date_of_issue').value },
      "date of expiry": { "text": document.getElementById('date_of_expiry').value }
    };
  
    $.ajax({
      url: `/documents/document/${docId}/update/`,
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(updatedData),
      headers: { 'X-CSRFToken': getCsrfToken() },
      success: function(response) {
        alert('Document data saved successfully!');
      },
      error: function(xhr, status, error) {
        console.error("Error saving document data:", error);
        alert('Failed to save document data. Please try again.');
      }
    });
  }
  
  // Get CSRF token from cookies
  function getCsrfToken() {
    let csrfToken = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 'csrftoken='.length) === 'csrftoken=') {
          csrfToken = decodeURIComponent(cookie.substring('csrftoken='.length));
          break;
        }
      }
    }
    return csrfToken;
  }
  
  // On page load, fetch document data and attach event listeners
  document.addEventListener('DOMContentLoaded', function() {
    const docId = "{{ document.id }}";  // Rendered by Django
    fetchDocumentData(docId);
    const saveButton = document.querySelector('.btn-primary');
    saveButton.addEventListener('click', function() {
      saveDocumentData(docId);
    });
  });
  