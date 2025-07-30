// Frontend input validation and XSS/NoSQL protection demo
function sanitizeInput(input) {
    // Remove script tags and suspicious patterns
    return input.replace(/<script.*?>.*?<\/script>/gi, '')
        .replace(/\$ne|\$eq|\$gt|\$lt|\$regex|\{|\}/gi, '')
        .replace(/alert\s*\(/gi, '');
}

function validateForm(form) {
    let valid = true;
    let errorMsg = '';
    form.querySelectorAll('input, textarea').forEach(function (field) {
        let sanitized = sanitizeInput(field.value);
        if (sanitized !== field.value) {
            valid = false;
            errorMsg = 'Malicious input detected and blocked.';
            field.value = sanitized;
        }
        // Basic XSS pattern check
        if (/script|<|>|alert|\$ne|\{|\}/i.test(field.value)) {
            valid = false;
            errorMsg = 'Security error: Invalid input.';
        }
    });
    if (!valid) {
        alert(errorMsg);
    }
    return valid;
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
});

// Show blocked attempts in real time
window.sanitizeInput = sanitizeInput;
window.validateForm = validateForm;
