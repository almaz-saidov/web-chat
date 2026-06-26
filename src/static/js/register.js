const signatureSamples = [];
const registerButton = document.querySelector('#registerForm button[type="submit"]');
const saveSignatureSampleButton = document.getElementById('saveSignatureSample');
const signatureProgress = document.getElementById('signatureProgress');

const signaturePad = createSignaturePad({
    canvasId: 'signatureCanvas',
    clearButtonId: 'clearSignature',
    errorElementId: 'error',
    onChange: updateSignatureState
});

function showError(message) {
    document.getElementById('success').style.display = 'none';
    document.getElementById('error').style.display = 'block';
    document.getElementById('error').textContent = message;
}

function showSuccess(message) {
    document.getElementById('error').style.display = 'none';
    document.getElementById('success').style.display = 'block';
    document.getElementById('success').textContent = message;
}

function getErrorMessage(error, fallbackMessage) {
    if (Array.isArray(error.detail) && error.detail.length > 0) {
        return error.detail[0].msg.replace(/^Value error,\s*/, '');
    }

    return error.detail || fallbackMessage;
}

function updateSignatureState() {
    signatureProgress.textContent = `Signature samples: ${signatureSamples.length}/5`;
    saveSignatureSampleButton.disabled = signatureSamples.length >= 5 || signaturePad.getPointCount() < 5;
    registerButton.disabled = signatureSamples.length !== 5;
}

saveSignatureSampleButton.addEventListener('click', function() {
    const signatureSample = signaturePad.getSample();
    if (!signatureSample) {
        showError('Signature sample is incomplete');
        return;
    }

    signatureSamples.push(signatureSample);
    signaturePad.clear();
    showSuccess(`Signature sample ${signatureSamples.length}/5 saved`);
    updateSignatureState();
});

document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const password_confirmation = document.getElementById('confirmPassword').value;

    if (password !== password_confirmation) {
        showError('Passwords do not match');
        return;
    }

    if (signatureSamples.length !== 5) {
        showError('Five signature samples are required');
        return;
    }

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username,
                password,
                password_confirmation,
                signature_samples: signatureSamples
            })
        });

        if (response.ok) {
            showSuccess('Registration successful!');

            setTimeout(() => {
                window.location.href = '/login.html';
            }, 1500);
        } else {
            const error = await response.json();
            showError(getErrorMessage(error, 'Registration error'));
        }
    } catch {
        showError('Connection error');
    }
});

updateSignatureState();
