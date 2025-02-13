// frontend/script.js

// Generate a random user ID for this session
const userId = 'user_' + Math.random().toString(36).substr(2, 9);
const API_BASE_URL = 'http://localhost:5001';

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const imageUploadButton = document.getElementById('image-upload');
const previewArea = document.getElementById('preview-area');

// Add initial welcome message
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const health = await response.json();
        
        if (health.status === 'healthy') {
            addMessage("Hi! I'm Plato, your AI print design assistant. I can help you with product information, pricing, and custom designs. What can I help you with today?", 'bot');
        } else {
            addMessage("Warning: System is currently unavailable. Please try again later.", 'system');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        addMessage("Warning: Unable to connect to the server. Please make sure the backend is running.", 'system');
    }
});

// Event Listeners
sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
});

// Image upload handling
imageUploadButton.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewArea.style.display = 'block';
            previewArea.innerHTML = `<img src="${e.target.result}" alt="Upload preview">`;
        };
        reader.readAsDataURL(file);

        // Store the file for sending later
        window.currentUpload = file;

    } catch (error) {
        console.error('Error processing image:', error);
        addMessage('Sorry, there was an error processing your image. Please try again.', 'system');
    }
});

async function sendMessage() {
    const message = chatInput.value.trim();
    const hasImage = window.currentUpload && previewArea.style.display === 'block';
    
    // Don't proceed if there's no message and no image
    if (!message && !hasImage) return;

    // If there's a message, add it to chat
    if (message) {
        addMessage(message, 'user');
    }

    // If there's an image in preview, add it to chat and try to upload it
    let designUrl = null;
    if (hasImage) {
        const previewImage = previewArea.querySelector('img');
        if (previewImage) {
            addProductImage(previewImage.src, 'User uploaded design');
            
            try {
                // Upload to Firebase first
                const uploadResult = await window.uploadDesignImage(window.currentUpload, userId);
                if (uploadResult.success) {
                    designUrl = uploadResult.url;
                } else {
                    throw new Error(uploadResult.error || 'Failed to upload image');
                }
            } catch (error) {
                console.error('Error uploading to Firebase:', error);
                addMessage('Sorry, there was an error uploading your design to storage. Please try again.', 'system');
                return;
            }
        }
    }

    // Clear input and preview
    chatInput.value = '';
    chatInput.style.height = 'auto';
    previewArea.style.display = 'none';
    previewArea.innerHTML = '';
    window.currentUpload = null;

    try {
        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Send message to backend - always include a message, even if it's just indicating an image upload
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message || "I'd like to share this design with you",
                user_id: userId,
                design_url: designUrl
            }),
        });

        // Remove typing indicator
        typingIndicator.remove();

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        
        // Add bot response text
        if (data.text) {
            addMessage(data.text, 'bot');
        }
        
        // Add product images if any
        if (data.images && data.images.length > 0) {
            data.images.forEach(image => {
                const imageUrl = `${API_BASE_URL}${image.url}`;
                addProductImage(imageUrl, image.alt);
            });
        }

    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again or check if the server is running.', 'bot');
    }
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

function addProductImage(url, alt) {
    const imageDiv = document.createElement('div');
    imageDiv.className = 'product-image';
    const img = document.createElement('img');
    img.src = url;
    img.alt = alt;
    imageDiv.appendChild(img);
    chatMessages.appendChild(imageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot typing';
    indicator.textContent = 'Plato is typing...';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return indicator;
}