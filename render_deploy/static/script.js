// API Configuration
const API_BASE_URL = window.location.origin;
const API_KEY = ''; // Add if needed

// State
let sessionData = {
    birthData: null,
    character: null,
    conversationHistory: []
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadCharacters();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('birthDetailsForm').addEventListener('submit', handleBirthDetailsSubmit);
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    document.getElementById('resetBtn').addEventListener('click', resetConsultation);
}

async function loadCharacters() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/characters`, {
            headers: API_KEY ? { 'X-API-Key': API_KEY } : {}
        });
        
        if (!response.ok) throw new Error('Failed to load characters');
        
        const data = await response.json();
        const select = document.getElementById('character');
        select.innerHTML = '';
        
        data.characters.forEach(char => {
            const option = document.createElement('option');
            option.value = char.id;
            option.textContent = `${char.emoji} ${char.name} - ${char.specialty}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading characters:', error);
        document.getElementById('character').innerHTML = '<option value="">Error loading characters</option>';
    }
}

function handleBirthDetailsSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        birth_date: document.getElementById('birthDate').value,
        birth_time: document.getElementById('birthTime').value,
        birth_place: document.getElementById('birthPlace').value,
        preferred_language: document.getElementById('language').value,
        character: document.getElementById('character').value
    };
    
    sessionData.birthData = formData;
    sessionData.character = formData.character;
    
    // Switch to chat view
    document.getElementById('birthDetailsSection').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    
    // Update astrologer name
    const selectedOption = document.getElementById('character').selectedOptions[0];
    document.getElementById('astrologerName').textContent = selectedOption.textContent;
    
    // Enable chat input
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    
    // Send initial greeting
    sendInitialMessage();
}

async function sendInitialMessage() {
    const greeting = `Namaste! I'm ready to provide you with Vedic astrology guidance. What would you like to know about your chart?`;
    addMessage('assistant', greeting);
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', message);
    input.value = '';
    
    // Show loading indicator
    showLoading(true);
    document.getElementById('sendBtn').disabled = true;
    
    try {
        // Prepare request payload
        const payload = {
            message: message,
            birth_data: {
                name: sessionData.birthData.name,
                birth_date: sessionData.birthData.birth_date,
                birth_time: sessionData.birthData.birth_time,
                birth_location: sessionData.birthData.birth_place
            },
            character_data: {
                character_name: sessionData.character,
                preferred_language: sessionData.birthData.preferred_language
            },
            conversation_history: sessionData.conversationHistory
        };
        
        // Make API request
        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(API_KEY ? { 'X-API-Key': API_KEY } : {})
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Add assistant response
            addMessage('assistant', data.response);
            
            // Update conversation history
            sessionData.conversationHistory.push({
                role: 'user',
                content: message
            });
            sessionData.conversationHistory.push({
                role: 'assistant',
                content: data.response
            });
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`);
    } finally {
        showLoading(false);
        document.getElementById('sendBtn').disabled = false;
        input.focus();
    }
}

function addMessage(role, content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'user' ? 'You' : 'Astrologer';
    
    const text = document.createElement('div');
    text.textContent = content;
    
    messageDiv.appendChild(label);
    messageDiv.appendChild(text);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

function resetConsultation() {
    if (confirm('Are you sure you want to start a new consultation?')) {
        sessionData = {
            birthData: null,
            character: null,
            conversationHistory: []
        };
        
        document.getElementById('chatSection').style.display = 'none';
        document.getElementById('birthDetailsSection').style.display = 'block';
        document.getElementById('chatMessages').innerHTML = '';
        document.getElementById('birthDetailsForm').reset();
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;
    }
}
