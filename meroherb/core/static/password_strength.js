// Password strength meter for signup page
// Place this in core/static/password_strength.js

document.addEventListener('DOMContentLoaded', function () {
    const passwordInput = document.querySelector('input[name="password1"]');
    // Remove strength bar, only show colored feedback

    // Use the static feedback div between password1 and password2 fields
    const feedback = document.getElementById('password-strength-feedback');
    if (feedback) {
        feedback.style.fontSize = '0.8rem';
        feedback.style.marginTop = '0px';
    }

    passwordInput.addEventListener('input', function () {
        const val = passwordInput.value;
        const score = getPasswordScore(val);
        updateFeedback(score);
        toggleButton(score);
    });

    function getPasswordScore(pw) {
        let score = 0;
        if (pw.length >= 8) score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/[a-z]/.test(pw)) score++;
        if (/[0-9]/.test(pw)) score++;
        if (/[^A-Za-z0-9]/.test(pw)) score++;
        if (pw.length >= 12) score++;
        return score;
    }

    function updateStrengthBar(score) {
        // Removed: no bar
    }

    function updateFeedback(score) {
        const pw = passwordInput.value;
        let text = '';
        let color = '';
        let missing = [];
        if (pw.length < 8) missing.push('at least 8 characters');
        if (!/[A-Z]/.test(pw)) missing.push('an uppercase letter');
        if (!/[a-z]/.test(pw)) missing.push('a lowercase letter');
        if (!/[0-9]/.test(pw)) missing.push('a number');
        if (!/[^A-Za-z0-9]/.test(pw)) missing.push('a special character');
        if (pw.length < 12) missing.push('12+ characters for best strength');

        if (score <= 2) {
            text = 'Weak password';
            color = '#d9534f';
        } else if (score <= 4) {
            text = 'Moderate password';
            color = '#f0ad4e';
        } else if (score <= 5) {
            text = 'Strong password';
            color = '#5cb85c';
        } else {
            text = 'Very strong password';
            color = '#27ae60';
        }
        if (missing.length > 0) {
            text += ' (add ' + missing.join(', ') + ')';
        }
        feedback.textContent = text;
        feedback.style.color = color;
    }

    function toggleButton(score) {
        const btn = document.querySelector('.signin-btn');
        if (score >= 5) {
            btn.disabled = false;
            btn.textContent = 'Create Account';
        } else {
            btn.disabled = true;
            btn.textContent = 'Use Strong Password';
        }
    }

    // Initial state
    updateFeedback(getPasswordScore(passwordInput.value));
    toggleButton(getPasswordScore(passwordInput.value));
});
