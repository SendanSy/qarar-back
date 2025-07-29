/**
 * Custom JavaScript for Django Unfold Admin
 * Handles RTL switching and Arabic language support
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get current language from Django
    const currentLang = document.documentElement.lang || 'en';
    
    // Set RTL for Arabic
    if (currentLang === 'ar') {
        document.documentElement.setAttribute('dir', 'rtl');
        document.body.setAttribute('dir', 'rtl');
    }
    
    // Language switcher functionality
    const langSwitcher = document.querySelector('.language-switcher');
    if (langSwitcher) {
        langSwitcher.addEventListener('change', function(e) {
            const selectedLang = e.target.value;
            // Update language preference
            fetch('/i18n/setlang/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: 'language=' + selectedLang
            }).then(() => {
                window.location.reload();
            });
        });
    }
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Auto-save draft posts
    const postForm = document.querySelector('form[data-model="post"]');
    if (postForm) {
        let autoSaveTimeout;
        const statusField = postForm.querySelector('select[name="status"]');
        
        // Only auto-save if status is draft
        if (statusField && statusField.value === 'draft') {
            const inputs = postForm.querySelectorAll('input[type="text"], textarea, select');
            
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    clearTimeout(autoSaveTimeout);
                    autoSaveTimeout = setTimeout(() => {
                        console.log('Auto-saving draft...');
                        // You can implement actual auto-save here
                    }, 3000);
                });
            });
        }
    }
    
    // Enhance file upload previews
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview element
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.style.maxWidth = '200px';
                    preview.style.marginTop = '10px';
                    
                    // Insert preview after input
                    const existingPreview = input.parentElement.querySelector('img.preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    preview.classList.add('preview');
                    input.parentElement.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });
    
    // Character counter for text fields
    const textFields = document.querySelectorAll('textarea[maxlength], input[type="text"][maxlength]');
    textFields.forEach(field => {
        const maxLength = field.getAttribute('maxlength');
        if (maxLength) {
            const counter = document.createElement('div');
            counter.className = 'character-counter';
            counter.style.fontSize = '0.875rem';
            counter.style.color = '#666';
            counter.style.marginTop = '5px';
            counter.style.textAlign = currentLang === 'ar' ? 'right' : 'left';
            
            const updateCounter = () => {
                const remaining = maxLength - field.value.length;
                counter.textContent = currentLang === 'ar' 
                    ? `${remaining} حرف متبقي` 
                    : `${remaining} characters remaining`;
            };
            
            field.addEventListener('input', updateCounter);
            field.parentElement.appendChild(counter);
            updateCounter();
        }
    });
});