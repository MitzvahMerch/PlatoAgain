// Initialize Firebase components
const db = firebase.firestore();
const storage = firebase.storage();

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
const uploadProgress = document.getElementById('upload-progress');
const progressText = uploadProgress.querySelector('.progress-text');
const progressFill = uploadProgress.querySelector('.progress-fill');

// Chat History Management
let chatHistory = [];
const MAX_HISTORY_LENGTH = 10;

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

// Enhanced file upload handling
imageUploadButton.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file
    if (!validateFile(file)) {
        return;
    }

    try {
        // Start upload process
        await handleFileUpload(file);
    } catch (error) {
        console.error('Error handling file:', error);
        addMessage('Sorry, there was an error processing your design. Please try again.', 'system');
        hideUploadProgress();
    }
});

// File validation
function validateFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (!validTypes.includes(file.type)) {
        addMessage('Please upload only images (JPEG, PNG, GIF) or PDF files.', 'system');
        return false;
    }

    if (file.size > maxSize) {
        addMessage('File size must be less than 5MB.', 'system');
        return false;
    }

    return true;
}

// File upload handling
async function handleFileUpload(file) {
    showUploadProgress();
    addMessage('Uploading your design...', 'system');

    const storageRef = storage.ref(`designs/${userId}/${file.name}`);
    const uploadTask = storageRef.put(file);

    // Track upload progress
    uploadTask.on('state_changed',
        (snapshot) => {
            const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            updateUploadProgress(progress);
        },
        (error) => {
            console.error('Upload error:', error);
            addMessage('Sorry, there was an error uploading your file. Please try again.', 'system');
            hideUploadProgress();
        },
        async () => {
            try {
                // Get download URL
                const downloadURL = await uploadTask.snapshot.ref.getDownloadURL();
                
                // Store metadata in Firestore
                await storeDesignMetadata(file, downloadURL);
                
                // Preview and process design
                await handleDesignSuccess(file, downloadURL);
            } catch (error) {
                console.error('Post-upload processing error:', error);
                addMessage('Your design was uploaded but there was an error during processing. Our team will review it manually.', 'system');
            }
            
            hideUploadProgress();
        }
    );
}

// Store design metadata in Firestore
async function storeDesignMetadata(file, downloadURL) {
    await db.collection('designs').add({
        userId: userId,
        fileName: file.name,
        fileType: file.type,
        fileSize: file.size,
        uploadDate: firebase.firestore.FieldValue.serverTimestamp(),
        downloadURL: downloadURL,
        placement: placementSelect.value,
        status: 'pending_review'
    });
}

// Handle successful design upload
async function handleDesignSuccess(file, downloadURL) {
    // Preview if it's an image
    if (file.type.startsWith('image/')) {
        designPreview.src = downloadURL;
        designPreview.style.display = 'block';
    }

    // Success message
    addMessage(`Design uploaded successfully! I'll help place it ${getPlacementText()} of your selected product.`, 'bot');

    // Process design
    await processDesign(downloadURL, file.name);
}

// Process uploaded design
async function processDesign(downloadURL, fileName) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/process-design`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: userId,
                designUrl: downloadURL,
                fileName: fileName,
                placement: placementSelect.value
            }),
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        
        // Update design status in Firestore
        await updateDesignStatus(downloadURL, data);

        // Handle processing results
        if (data.suggestions) {
            addMessage(data.suggestions, 'bot');
        }

    } catch (error) {
        console.error('Error processing design:', error);
        addMessage('Your design was uploaded but there was an error during processing. Our team will review it manually.', 'bot');
    }
}

// Update design status in Firestore
async function updateDesignStatus(downloadURL, processingData) {
    const designsRef = db.collection('designs');
    const query = await designsRef.where('downloadURL', '==', downloadURL).limit(1).get();
    
    if (!query.empty) {
        await query.docs[0].ref.update({
            status: 'processed',
            processedData: processingData
        });
    }
}

// Message handling
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    updateChatHistory('user', message);

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';

    try {
        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Send message to backend
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: userId,
                chat_history: chatHistory
            }),
        });

        // Remove typing indicator
        typingIndicator.remove();

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        
        // Add bot response
        if (data.text) {
            addMessage(data.text, 'bot');
            updateChatHistory('bot', data.text);
        }
        
        // Handle product images
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

// Chat history management
function updateChatHistory(role, content) {
    chatHistory.push({ role, content });
    if (chatHistory.length > MAX_HISTORY_LENGTH) {
        chatHistory.shift();
    }
}

// UI Helper Functions
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

// Upload Progress UI Functions
function showUploadProgress() {
    uploadProgress.style.display = 'block';
    progressText.textContent = 'Starting upload...';
    progressFill.style.width = '0%';
}

function updateUploadProgress(percent) {
    progressText.textContent = `Upload progress: ${Math.round(percent)}%`;
    progressFill.style.width = `${percent}%`;
}

function hideUploadProgress() {
    uploadProgress.style.display = 'none';
}

function getPlacementText() {
    const placement = placementSelect.value;
    switch (placement) {
        case 'chest':
            return 'on the front right chest';
        case 'back':
            return 'on the full back';
        case 'sleeve':
            return 'on the sleeve';
        default:
            return 'on your selected location';
    }
}