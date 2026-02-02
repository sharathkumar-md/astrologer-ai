// API Configuration
const API_BASE_URL = window.location.origin;
const API_KEY = ''; // Add if needed

// State
let sessionData = {
    birthData: null,
    character: null,
    promptVersion: 'current',
    conversationHistory: [],
    sessionId: null,  // Track session ID
    userId: null      // Track user ID
};

// Store prompts data for descriptions
let promptsData = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadCharacters();
    loadPrompts();
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

async function loadPrompts() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/prompts`, {
            headers: API_KEY ? { 'X-API-Key': API_KEY } : {}
        });

        if (!response.ok) throw new Error('Failed to load prompts');

        const data = await response.json();
        const select = document.getElementById('promptVersion');
        select.innerHTML = '';

        // Store prompts data for descriptions
        data.prompts.forEach(prompt => {
            promptsData[prompt.id] = prompt;
            const option = document.createElement('option');
            option.value = prompt.id;
            option.textContent = prompt.name;
            select.appendChild(option);
        });

        // Show description for first prompt
        if (data.prompts.length > 0) {
            document.getElementById('promptDescription').textContent = data.prompts[0].description;
        }

        // Add change listener to show description
        select.addEventListener('change', function() {
            const selectedPrompt = promptsData[this.value];
            if (selectedPrompt) {
                document.getElementById('promptDescription').textContent = selectedPrompt.description;
            }
        });
    } catch (error) {
        console.error('Error loading prompts:', error);
        document.getElementById('promptVersion').innerHTML = '<option value="current">Current (Default)</option>';
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
        character: document.getElementById('character').value,
        prompt_version: document.getElementById('promptVersion').value
    };

    sessionData.birthData = formData;
    sessionData.character = formData.character;
    sessionData.promptVersion = formData.prompt_version;
    
    // Switch to chat view
    document.getElementById('birthDetailsSection').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    
    // Update astrologer name
    const selectedOption = document.getElementById('character').selectedOptions[0];
    document.getElementById('astrologerName').textContent = selectedOption.textContent;

    // Show prompt version being used
    const selectedPrompt = promptsData[sessionData.promptVersion];
    if (selectedPrompt) {
        document.getElementById('promptVersionLabel').textContent = `Testing: ${selectedPrompt.name}`;
    }
    
    // Enable chat input
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
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
            session_id: sessionData.sessionId,  // Send session ID to maintain history
            prompt_version: sessionData.promptVersion  // Send prompt version for A/B testing
        };
        
        // Make API request
        const response = await fetch(`${API_BASE_URL}/api/v1/chat/simple`, {
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
            // Save session and user IDs from first response
            if (data.session_id && !sessionData.sessionId) {
                sessionData.sessionId = data.session_id;
                console.log('Session ID:', sessionData.sessionId);
            }
            if (data.user_id && !sessionData.userId) {
                sessionData.userId = data.user_id;
                console.log('User ID:', sessionData.userId);
            }
            
            // Split response by ||| and add as separate messages
            const messages = data.response.split('|||').map(msg => msg.trim()).filter(msg => msg.length > 0);
            
            messages.forEach((msg, index) => {
                setTimeout(() => {
                    addMessage('assistant', msg);
                }, index * 800); // 800ms delay between each message for natural feel
            });
            
            // No need to track history manually - database handles it!
            // But keep for UI display consistency
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
            promptVersion: 'current',
            conversationHistory: [],
            sessionId: null,
            userId: null
        };
        
        document.getElementById('chatSection').style.display = 'none';
        document.getElementById('birthDetailsSection').style.display = 'block';
        document.getElementById('chatMessages').innerHTML = '';
        document.getElementById('birthDetailsForm').reset();
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;
    }
}
