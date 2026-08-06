let token = localStorage.getItem('access_token');

if (!token) {
    window.location.href = 'login.html';
}

let ws = null;
let isConnected = false;

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function addMessage(messageData) {
    const messagesContainer = document.getElementById('messagesContainer');

    const loadingEl = document.getElementById('loadingMessages');
    if (loadingEl) {
        loadingEl.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';

    const header = document.createElement('div');
    header.className = 'message-header';

    const author = document.createElement('span');
    author.className = 'message-author';
    author.textContent = messageData.username || 'Unknown';

    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = formatTime(messageData.created_at);

    header.appendChild(author);
    header.appendChild(time);

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = messageData.content;

    messageDiv.appendChild(header);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);

    const shouldScroll = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 100;
    if (shouldScroll) {
        scrollToBottom();
    }
}

async function loadMessageHistory() {
    try {
        let response = await fetch('/api/messages', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            const error = await response.json();

            if (error.detail === 'Invalid token') {
                await logout();
            } else if (error.detail === 'Access token expired') {
                await refresh();
                response = await fetch('/api/messages', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        }

        const messages = await response.json();

        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '';

        messages.forEach(message => addMessage(message));

        scrollToBottom();

        return messages;
    } catch (error) {
        console.error('Error loading messages:', error);
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '<div class="loading">Failed to load messages. Please refresh the page.</div>';

        if (error.message === 'Failed to load messages') {
            await logout();
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    const sendBtn = document.getElementById('sendBtn');

    if (!message) return;

    try {
        sendBtn.disabled = true;
        input.disabled = true;

        let response = await fetch('/api/messages', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: message
            })
        });

        if (response.status === 401) {
            const error = await response.json();

            if (error.detail === 'Invalid token') {
                await logout();
            } else if (error.detail === 'Access token expired') {
                await refresh();
                response = await fetch('/api/messages', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        content: message
                    })
                });
            }
        }

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(message);
        }

        input.value = '';

    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        sendBtn.disabled = false;
        input.disabled = false;
        input.focus();
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function initWebSocket() {
    token = localStorage.getItem('access_token');
    ws = new WebSocket(`ws://${window.location.host}/api/ws?token=${token}`);

    ws.onopen = function() {
        isConnected = true;

        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('messageInput').focus();
    };

    ws.onerror = async function() {
        await refresh();
        isConnected = false;
    };

    ws.onclose = function() {
        isConnected = false;

        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;

        setTimeout(() => {
            if (!isConnected && token) {
                initWebSocket();
            }
        }, 3000);
    };

    ws.onmessage = function(event) {
        try {
            const messageText = event.data;

            const colonIndex = messageText.indexOf(': ');
            if (colonIndex > 0) {
                const username = messageText.substring(0, colonIndex);
                const content = messageText.substring(colonIndex + 2);

                addMessage({
                    username: username,
                    content: content,
                    created_at: new Date().toISOString()
                });
            } else {
                addMessage({
                    username: 'System',
                    content: messageText,
                    created_at: new Date().toISOString()
                });
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };
}

async function refresh() {
    localStorage.removeItem('access_token');

    const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    });

    if (response.status === 401) {
        await logout();
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_type', data.token_type);
    initWebSocket();
    await loadMessageHistory();
}

async function logout() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }

    localStorage.removeItem('access_token');

    await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        credentials: 'same-origin'
    });

    window.location.href = 'login.html';
}

document.getElementById('logoutBtn').addEventListener('click', logout);
document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !this.disabled) {
        sendMessage();
    }
});

async function init() {
    await loadMessageHistory();

    initWebSocket();
}

init();
