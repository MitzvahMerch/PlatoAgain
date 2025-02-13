// script.js
import { uploadDesignImage } from './firebase-config.js';

// Generate a random user ID for this session
const userId = 'user_' + Math.random().toString(36).substr(2, 9);
const API_BASE_URL = 'http://localhost:5001';

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const imageUploadButton = document.getElementById('image-upload');
const designPreview = document.getElementById('design-preview');
const placementSelect = document.getElementById('placement-select');
const uploadProgress = document.querySelector('.upload-progress');
const progressBar = document.querySelector('.progress-bar');
const progressText = document.querySelector('.progress-text');
const previewInfo = document.querySelector('.preview-info');

let currentDesignUrl = null;

// Welcome message and health check
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
        // Show loading state
        uploadProgress.style.display = 'block';
        addMessage('Uploading your design...', 'system');

        // Upload to Firebase
        const uploadResult = await uploadDesignImage(file, userId);

        if (uploadResult.success) {
            // Update preview
            designPreview.src = uploadResult.url;
            designPreview.style.display = 'block';
            currentDesignUrl = uploadResult.url;

            // Update progress and info
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            previewInfo.textContent = `Design uploaded successfully! Location: ${placementSelect.value === 'chest' ? 'Front Right Chest' : 'Full Back'}`;

            // Add success message
            addMessage(`Design uploaded successfully! I'll help place it ${placementSelect.value === 'chest' ? 'on the front right chest' : 'on the full back'} of your selected product.`, 'bot');
        } else {
            throw new Error(uploadResult.error);
        }

    } catch (error) {
        console.error('Error uploading image:', error);
        addMessage('Sorry, there was an error uploading your design. Please try again.', 'bot');
        uploadProgress.style.display = 'none';
    }
});

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';

    try {
        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Send message to backend with design info if available
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: userId,
                design_url: currentDesignUrl,
                design_placement: placementSelect.value
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