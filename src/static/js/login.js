const loginButton = document.querySelector('#loginForm button[type="submit"]');
const errorElement = document.getElementById('error');

const signaturePad = createSignaturePad({
    canvasId: 'signatureCanvas',
    clearButtonId: 'clearSignature',
    errorElementId: 'error',
    onChange: updateLoginState
});

function showError(message) {
    errorElement.style.display = 'block';
    errorElement.textContent = message;
}

function getErrorMessage(error, fallbackMessage) {
    if (Array.isArray(error.detail) && error.detail.length > 0) {
        return error.detail[0].msg.replace(/^Value error,\s*/, '');
    }

    return error.detail || fallbackMessage;
}

function updateLoginState() {
    loginButton.disabled = signaturePad.getPointCount() < 5;
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const signatureSample = signaturePad.getSample();

    if (!signatureSample) {
        showError('Signature sample is incomplete');
        return;
    }

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username,
                password,
                signature_sample: signatureSample
            })
        });

        if (response.ok) {
            const data = await response.json();

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('token_type', data.token_type);

            window.location.href = '/chat.html';
        } else {
            const error = await response.json();
            showError(getErrorMessage(error, 'Invalid username, password or signature'));
        }
    } catch {
        showError('Connection error');
    }
});

document.getElementById('username').focus();
updateLoginState();
