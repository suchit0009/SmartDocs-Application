// static/js/base.js

// Navigation
function selectSection(navItem) {
    const sectionId = navItem.getAttribute('data-section');
    // If not on the home page, redirect to home with section
    if (window.location.pathname !== '/home/') {
        window.location.href = `/home/#${sectionId}`;
        return;
    }
    // On home page, toggle sections
    const contentSections = document.querySelectorAll('.content-section');
    if (contentSections.length === 0) return;
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    navItem.classList.add('active');
    contentSections.forEach(section => section.classList.remove('active'));
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
}

// Attach navigation event listeners
document.querySelectorAll('.nav-item').forEach(navItem => {
    navItem.addEventListener('click', () => selectSection(navItem));
});

// Logout
function logout() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/accounts/logout/';
    const csrfToken = document.createElement('input');
    csrfToken.type = 'hidden';
    csrfToken.name = 'csrfmiddlewaretoken';
    csrfToken.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
    form.appendChild(csrfToken);
    document.body.appendChild(form);
    form.submit();
}

// Loading overlay (for pages that include it)
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
}

// Handle hash-based navigation on page load (for home page)
window.addEventListener('load', () => {
    if (window.location.pathname === '/home/' && window.location.hash) {
        const sectionId = window.location.hash.replace('#', '');
        const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
        if (navItem) selectSection(navItem);
    }
});