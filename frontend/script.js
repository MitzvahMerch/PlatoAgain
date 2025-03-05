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
let currentProductBackImageUrl = null;

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
            addMessage("Hey! I'm Plato. I specialize in making bulk custom ordering as simple as it should be. Just talk to me like a friend and I'll finalize your order in seconds. Let's start off with finding a product, what type of clothing, and in what color, are you looking to customize today?", 'bot');
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
        
        // Store the upload result globally
        window.currentUploadResult = uploadResult;

        // Show placement modal with DesignPlacer
        const root = ReactDOM.createRoot(window.placementModal.content);
        root.render(
            React.createElement(window.DesignPlacer, {
                frontImage: currentProductImageUrl,
                backImage: currentProductBackImageUrl,
                designUrl: uploadResult.url,
                onSave: svgBasedCompositeRenderer
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
                if (image.type === 'product_front') {
                    currentProductImageUrl = imageUrl;
                } else if (image.type === 'product_back') {
                    currentProductBackImageUrl = imageUrl;
                }
                addProductImage(imageUrl, image.alt);
            });
        }

        // Check for action directives from the backend
        if (data.action && data.action.type === 'showShippingModal') {
            // Show the shipping modal with order details
            window.shippingModal.show(data.action.orderDetails);
            
            // NOTE: Address autocomplete is now handled directly in the shippingModal.js
            
            // Handle form submission
            // Update the form submission handler in script.js to include the receivedByDate field
// This code is intended to replace the relevant section in script.js

// Inside the sendMessage function where the shipping modal form submission is handled:

// Handle form submission
window.shippingModal.form.onsubmit = async function(e) {
    e.preventDefault();
    
    // Get form data
    const formData = window.shippingModal.getFormData();
    
    // Hide the modal
    window.shippingModal.hide();
    
    // Show a loading indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        // Send data to backend
        const response = await fetch(`${API_BASE_URL}/api/submit-order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                name: formData.name,
                address: formData.address,
                email: formData.email,
                receivedByDate: formData.receivedByDate
            }),
        });
        
        typingIndicator.remove();
        
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display the response (order confirmation)
        if (data.text) {
            addMessage(data.text, 'bot');
        }
        
    } catch (error) {
        console.error('Error submitting order:', error);
        typingIndicator.remove();
        addMessage('Sorry, I encountered an error processing your order. Please try again.', 'bot');
    }
};
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

// SVG-based composite renderer function
Copy// SVG-based composite renderer function
async function svgBasedCompositeRenderer(placement) {
    try {
        // Extract SVG coordinates from the placement data
        const { svgCoordinates, showBackImage, designUrl } = placement;
        
        if (!svgCoordinates) {
            console.error('SVG coordinates not found in placement data');
            throw new Error('Missing SVG coordinate data needed for visual capture');
        }
        
        // Create a canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Load the original product and design images
        const [originalProductImg, designImg] = await Promise.all([
            loadImage(showBackImage ? currentProductBackImageUrl : currentProductImageUrl),
            loadImage(designUrl)
        ]);
        
        // Set canvas to match the actual product image size
        canvas.width = originalProductImg.width;
        canvas.height = originalProductImg.height;
        
        // Draw the product
        ctx.drawImage(originalProductImg, 0, 0);
        
        // Extract SVG positioning information
        const { 
            x, y, width, height,  // Position and size in SVG coordinates
            centerX, centerY,     // Center point in SVG coordinates
            viewBoxWidth, viewBoxHeight  // SVG viewBox dimensions
        } = svgCoordinates;
        
        // Calculate scaling factors from SVG to actual product image
        // Calculate scaling factors from SVG to actual product image
// These should now be nearly identical since we matched aspect ratios
const scaleX = originalProductImg.width / viewBoxWidth;
const scaleY = originalProductImg.height / viewBoxHeight;

console.log('Aspect ratio check:', {
    svg: viewBoxHeight / viewBoxWidth,
    product: originalProductImg.height / originalProductImg.width,
    scaleFactors: { scaleX, scaleY }
});

// Convert SVG coordinates to actual image pixels using X scale for both dimensions
// to maintain the aspect ratio as seen in the preview
const actualWidth = width * scaleX;
const actualHeight = height * scaleX;

// Calculate the center position in actual pixels
const actualCenterX = centerX * scaleX;
const actualCenterY = centerY * scaleY;

// Calculate the top-left position from the center
const actualX = actualCenterX - (actualWidth / 2);
const actualY = actualCenterY - (actualHeight / 2);
        
        // Log the conversion details
        console.log('SVG to Canvas conversion (preserving aspect ratio):', {
            svgCoordinates,
            actualCoordinates: {
                x: actualX,
                y: actualY,
                width: actualWidth,
                height: actualHeight,
                center: { x: actualCenterX, y: actualCenterY }
            },
            scaling: {
                scaleX,
                scaleY
            },
            images: {
                product: {
                    width: originalProductImg.width,
                    height: originalProductImg.height
                },
                design: {
                    width: designImg.width,
                    height: designImg.height
                }
            }
        });
        
        // Draw the design at the calculated position and size
        ctx.drawImage(designImg, actualX, actualY, actualWidth, actualHeight);
        
        // Create and upload composite
        const blob = await new Promise(resolve => 
            canvas.toBlob(resolve, 'image/png')
        );
        
        // Use the globally stored upload result
        if (!window.currentUploadResult || !window.currentUploadResult.path) {
            throw new Error('Upload information not available');
        }
        
        // Generate path for the composite image
        const originalPath = window.currentUploadResult.path;
        const folderPath = originalPath.substring(0, originalPath.lastIndexOf('/'));
        const originalFileName = originalPath.split('/').pop();
        const compositeFileName = `composite_${Date.now()}_${originalFileName}`;
        const compositePath = `${folderPath}/${compositeFileName}`;
        
        // Upload to Firebase Storage
        const compositeRef = window.storage.ref(compositePath);
        await compositeRef.put(blob);
        const compositeUrl = await compositeRef.getDownloadURL();
        
        // Close modal and show result
        window.placementModal.hide();
        addProductImage(compositeUrl, 'Design placement preview');
        await sendMessage();
        
    } catch (error) {
        console.error('Error saving placement:', error);
        addMessage('Sorry, there was an error saving your design placement. Please try again.', 'system');
    }
}