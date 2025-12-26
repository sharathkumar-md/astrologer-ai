let currentUserId = null;

// Page Navigation
function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tab + 'Tab').classList.add('active');
    event.target.classList.add('active');
    
    if (tab === 'load') {
        loadUsersList();
    }
}

function showChatPage() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('chatPage').classList.add('active');
}

function logout() {
    currentUserId = null;
    document.getElementById('chatBox').innerHTML = `
        <div class="welcome-message">
            <h3>Welcome! 🌙</h3>
            <p>Ask me anything about your astrological journey</p>
        </div>
    `;
    document.getElementById('messageInput').value = '';
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('chatPage').classList.remove('active');
}

// Create User
async function createUser(event) {
    event.preventDefault();
    
    const name = document.getElementById('name').value.trim();
    const birthDate = document.getElementById('birthDate').value.trim();
    const birthTime = document.getElementById('birthTime').value.trim();
    const location = document.getElementById('location').value.trim();
    
    try {
        const response = await fetch('/api/create-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name, date: birthDate, time: birthTime, location
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUserId = data.user_id;
            document.getElementById('userName').textContent = name;
            document.getElementById('userLocation').textContent = location;
            showChatPage();
            document.getElementById('createForm').reset();
            // Clear chat
            document.getElementById('chatBox').innerHTML = `
                <div class="welcome-message">
                    <h3>Welcome! 🌙</h3>
                    <p>Ask me anything about your astrological journey</p>
                </div>
            `;
        } else {
            alert('Error: ' + (data.error || 'Failed to create chart'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Load Users List
async function loadUsersList() {
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        
        const usersList = document.getElementById('usersList');
        const noUsers = document.getElementById('noUsers');
        
        if (data.users && data.users.length > 0) {
            usersList.innerHTML = '';
            noUsers.style.display = 'none';
            
            data.users.forEach(user => {
                const card = document.createElement('div');
                card.className = 'user-card';
                card.onclick = () => selectUser(user.id, user.name, user.location);
                card.innerHTML = `
                    <h4>${user.name}</h4>
                    <p>📍 ${user.location}</p>
                    <p style="font-size: 0.85em; color: #999;">Saved: ${user.created_at || 'Recently'}</p>
                `;
                usersList.appendChild(card);
            });
        } else {
            usersList.innerHTML = '';
            noUsers.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Select User
async function selectUser(userId, name, location) {
    try {
        const response = await fetch(`/api/load-user/${userId}`);
        const data = await response.json();
        
        if (response.ok) {
            currentUserId = userId;
            document.getElementById('userName').textContent = name;
            document.getElementById('userLocation').textContent = location;
            showChatPage();
        } else {
            alert('Error loading user: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Send Message
async function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    if (!currentUserId) {
        alert('Please select or create a user first');
        return;
    }
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    messageInput.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                message: message
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Process response (split by ||| for multiple messages)
            const responses = data.response.split('|||').map(r => r.trim()).filter(r => r);
            responses.forEach(resp => {
                addMessageToChat(resp, 'assistant');
            });
        } else {
            addMessageToChat('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        addMessageToChat('Connection error. Please try again.', 'assistant');
    }
}

// Add Message to Chat
function addMessageToChat(message, sender) {
    const chatBox = document.getElementById('chatBox');
    
    // Remove welcome message if present
    const welcomeMsg = chatBox.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Focus on first input
    document.getElementById('name').focus();
});
