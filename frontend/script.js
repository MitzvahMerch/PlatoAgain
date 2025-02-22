// Helper function for image loading
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = "anonymous";  // Add this line
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

// Generate a random user ID for this session
const userId = 'user_' + Math.random().toString(36).substr(2, 9);
const API_BASE_URL = 'http://localhost:5001';
let currentProductImageUrl = null;  // Add this variable to store front product image

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const imageUploadButton = document.getElementById('image-upload');

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

// Image upload handling with design placement
imageUploadButton.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        // Store file and update UI
        window.currentUpload = file;
        const uploadButton = document.querySelector('.chat-upload-button svg');
        uploadButton.innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
        uploadButton.style.color = 'var(--success-color)';
        
        // Upload the file first
        const uploadResult = await window.uploadDesignImage(file, userId);
        if (!uploadResult.success) {
            throw new Error(uploadResult.error || 'Failed to upload image');
        }

        // Show placement modal with DesignPlacer
        const root = ReactDOM.createRoot(window.placementModal.content);
        root.render(
            React.createElement(window.DesignPlacer, {
                productImage: currentProductImageUrl,  // Use stored product image URL
                designUrl: uploadResult.url,
                onSave: async (placement) => {
                    try {
                        // Create canvas for composite
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        
                        // Load both images
                        const [productImg, designImg] = await Promise.all([
                            loadImage(currentProductImageUrl),  // Use stored product image URL
                            loadImage(uploadResult.url)
                        ]);
                        
                        // Set canvas size
                        canvas.width = productImg.width;
                        canvas.height = productImg.height;
                        
                        // Draw product
                        ctx.drawImage(productImg, 0, 0);
                        
                        // Apply design transformations
                        ctx.save();
                        ctx.translate(placement.position.x, placement.position.y);
                        ctx.scale(placement.scale, placement.scale);
                        ctx.translate(-designImg.width/2, -designImg.height/2);
                        ctx.drawImage(designImg, 0, 0);
                        ctx.restore();
                        
                        // Create composite file
                        const blob = await new Promise(resolve => 
                            canvas.toBlob(resolve, 'image/png')
                        );
                        
                        // Create path for composite in same folder
                        const originalPath = uploadResult.path;
                        const folderPath = originalPath.substring(0, originalPath.lastIndexOf('/'));
                        const originalFileName = originalPath.split('/').pop();
                        const compositeFileName = `composite_${Date.now()}_${originalFileName}`;
                        const compositePath = `${folderPath}/${compositeFileName}`;
                        
                        // Upload composite
                        const compositeRef = window.storage.ref(compositePath);
                        await compositeRef.put(blob);
                        const compositeUrl = await compositeRef.getDownloadURL();
                        
                        // Hide modal
                        window.placementModal.hide();
                        
                        // Show the composite in chat
                        addProductImage(compositeUrl, 'Design placement preview');
                        
                        // Continue with chat flow
                        await sendMessage();
                        
                    } catch (error) {
                        console.error('Error saving placement:', error);
                        addMessage('Sorry, there was an error saving your design placement. Please try again.', 'system');
                    }
                }
            })
        );
        
        window.placementModal.show();
        
    } catch (error) {
        console.error('Error processing image:', error);
        addMessage('Sorry, there was an error processing your image. Please try again.', 'system');
    }
});

async function sendMessage() {
    const message = chatInput.value.trim();
    const hasImage = window.currentUpload;
    
    if (!message && !hasImage) return;

    if (message) {
        addMessage(message, 'user');
    }

    chatInput.value = '';
    chatInput.style.height = 'auto';
    window.currentUpload = null;

    const uploadButton = document.querySelector('.chat-upload-button svg');
    uploadButton.innerHTML = `
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
    `;
    uploadButton.style.color = 'var(--secondary-color)';

    try {
        const typingIndicator = addTypingIndicator();

        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message || "I'd like to share this design with you",
                user_id: userId,
            }),
        });

        typingIndicator.remove();

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        
        if (data.text) {
            addMessage(data.text, 'bot');
        }
        
        if (data.images && data.images.length > 0) {
            data.images.forEach(image => {
                const imageUrl = `${API_BASE_URL}${image.url}`;
                if (image.type === 'product_front') {  // Store front image URL
                    currentProductImageUrl = imageUrl;
                }
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