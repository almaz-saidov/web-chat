document.getElementById('loginForm').onsubmit = async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });

        if (response.ok) {
            const data = await response.json();

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('token_type', data.token_type);

            window.location.href = '/chat.html';
        } else {
            const error = await response.json();
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').textContent = error.detail || 'Invalid username or password';
        }
    } catch {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'Connection error';
    }
};

document.getElementById('username').focus();
