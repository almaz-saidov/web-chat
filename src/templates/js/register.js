document.getElementById('registerForm').onsubmit = async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const password_confirmation = document.getElementById('confirmPassword').value;

    if (password !== password_confirmation) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'Passwords do not match';
        return;
    }

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username,
                password,
                password_confirmation
            })
        });

        if (response.ok) {
            document.getElementById('error').style.display = 'none';
            document.getElementById('success').style.display = 'block';
            document.getElementById('success').textContent = 'Registration successful!';

            setTimeout(() => {
                window.location.href = '/login.html';
            }, 1500);
        } else {
            const error = await response.json();
            document.getElementById('error').style.display = 'block';

            if (response.status === 422 && error.detail) {
                const validationError = error.detail.find(err => err.loc.includes('username'));
                if (validationError) {
                    const errorMessage = validationError.msg.replace(/^Value error,\s*/, '');
                    document.getElementById('error').textContent = errorMessage;
                } else {
                    document.getElementById('error').textContent = error.detail || 'Registration error';
                }
            } else {
                document.getElementById('error').textContent = error.detail || 'Registration error';
            }
        }
    } catch {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'Connection error';
    }
};
