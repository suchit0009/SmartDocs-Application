// Navigation Toggle
const mobileToggle = document.getElementById('mobileToggle');
const navLinks = document.getElementById('navLinks');

mobileToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});

// Testimonial Slider
const track = document.getElementById('testimonialsTrack');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const indicators = document.querySelectorAll('.indicator');

let currentIndex = 0;

function updateSlider() {
    track.style.transform = `translateX(-${currentIndex * 100}%)`;
    
    indicators.forEach((indicator, index) => {
        if (index === currentIndex) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    });
}

prevBtn.addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + 3) % 3;
    updateSlider();
});

nextBtn.addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % 3;
    updateSlider();
});

indicators.forEach(indicator => {
    indicator.addEventListener('click', () => {
        currentIndex = parseInt(indicator.getAttribute('data-index'));
        updateSlider();
    });
});

setInterval(() => {
    currentIndex = (currentIndex + 1) % 3;
    updateSlider();
}, 5000);

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (this.getAttribute('href') === '#') return;
        
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });
            
            navLinks.classList.remove('active');
        }
    });
});

// Animation on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.feature-card, .section-title, .section-subtitle, .testimonial, .cta-title, .cta-description, .cta-btn, .enquiry-content, .enquiry-form');
    
    elements.forEach(element => {
        const elementPosition = element.getBoundingClientRect().top;
        const screenPosition = window.innerHeight;
        
        if (elementPosition < screenPosition - 100) {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }
    });
}

document.querySelectorAll('.feature-card, .section-title, .section-subtitle, .testimonial, .cta-title, .cta-description, .cta-btn, .enquiry-content, .enquiry-form').forEach(element => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = 'all 0.6s ease-out';
});

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);
