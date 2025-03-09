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
let designsAdded = 0; // Track how many designs have been added

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
            addMessage("Hey! I'm Plato. Talk to me like a friend and I'll finalize your bulk custom clothing order in seconds. What type of clothing, and in what color, are you looking to customize today?", 'bot');
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
            const botMessage = addMessage(data.text, 'bot');
            
            // Check if the message contains a PayPal invoice URL
            if (data.text.includes('https://www.paypal.com/invoice/p/#')) {
                // If we have the paypalIntegration component, inject it into the message
                if (window.paypalIntegration && typeof window.paypalIntegration.injectIntoMessage === 'function') {
                    window.paypalIntegration.injectIntoMessage(botMessage);
                } else {
                    console.error('PayPal integration component not available');
                }
            }
        }
        if (data.action) {
            // Get the last bot message for injecting UI elements
            const lastMessage = document.querySelector('#chat-messages .message.bot:last-child');
            if (lastMessage) {
                // Store the action data in the message element's dataset for potential future use
                lastMessage.dataset.action = JSON.stringify(data.action);
                
                // Handle different action types
                if (data.action.type === 'showShippingModal') {
                    // Inject the shipping form directly into the message
                    if (window.shippingForm && typeof window.shippingForm.injectIntoMessage === 'function') {
                        window.shippingForm.injectIntoMessage(lastMessage, data.action.orderDetails);
                    } else {
                        console.error('Shipping form component not available');
                        addMessage('Sorry, I encountered an error with the shipping form. Please refresh the page and try again.', 'system');
                    }
                } else if (data.action.type === 'showProductOptions') {
                    // Inject product selection buttons into the message
                    if (window.productButtons && typeof window.productButtons.injectIntoMessage === 'function') {
                        window.productButtons.injectIntoMessage(lastMessage, data.action.productInfo);
                    } else {
                        console.error('Product buttons component not available');
                    }
                }
            } else {
                console.error('No bot message found to inject UI elements');
                addMessage('Sorry, I couldn\'t display the interactive elements. Please try again.', 'bot');
            }
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
            // Get the last bot message to inject the shipping form
            const lastMessage = document.querySelector('#chat-messages .message.bot:last-child');
            if (lastMessage) {
                // Store the action data in the message element's dataset for potential future use
                lastMessage.dataset.action = JSON.stringify(data.action);
                
                // Inject the shipping form directly into the message
                if (window.shippingForm && typeof window.shippingForm.injectIntoMessage === 'function') {
                    window.shippingForm.injectIntoMessage(lastMessage, data.action.orderDetails);
                } else {
                    console.error('Shipping form component not available');
                    addMessage('Sorry, I encountered an error with the shipping form. Please refresh the page and try again.', 'system');
                }
            } else {
                console.error('No bot message found to inject shipping form');
                addMessage('Sorry, I couldn\'t display the shipping form. Please try again.', 'system');
            }
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
    
    // Check if this is a bot message about quantity selection
    if (sender === 'bot') {
        const messageText = content.toLowerCase();
        
        // Check for messages asking about quantities with size information
        if (messageText.includes('how many of each size would you like to order') && 
            (messageText.includes('youth sizes') || messageText.includes('adult sizes'))) {
            
            console.log('Quantity prompt detected, injecting selector...');
            
            // Inject the quantity selector into this message
            if (window.quantitySelector && typeof window.quantitySelector.injectIntoMessage === 'function') {
                window.quantitySelector.injectIntoMessage(messageDiv);
            }
        }
    }
    
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

// New function to show design options dialog
function showDesignOptionsDialog(compositeUrl, wasBackImage) {
    // Create dialog container
    const dialogOverlay = document.createElement('div');
    dialogOverlay.className = 'design-options-overlay';
    dialogOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    `;
    
    const dialogContent = document.createElement('div');
    dialogContent.className = 'design-options-content';
    dialogContent.style.cssText = `
        width: 400px;
        padding: 20px;
        background: #222;
        border-radius: 8px;
        text-align: center;
        color: white;
    `;
    
    const dialogHeader = document.createElement('h3');
    dialogHeader.textContent = 'Design Added Successfully!';
    dialogHeader.style.cssText = `
        margin-top: 0;
        margin-bottom: 20px;
        color: var(--primary-color);
    `;
    
    const dialogText = document.createElement('p');
    dialogText.textContent = 'What would you like to do next?';
    
    // Add another design button
    const addMoreBtn = document.createElement('button');
    addMoreBtn.textContent = 'Add Another Design';
    addMoreBtn.style.cssText = `
        padding: 12px 20px;
        margin: 10px;
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
    `;
    
    // Finalize button
    const finalizeBtn = document.createElement('button');
    finalizeBtn.textContent = 'Finalize Customization';
    finalizeBtn.style.cssText = `
        padding: 12px 20px;
        margin: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
    `;
    
    // Assemble dialog
    dialogContent.appendChild(dialogHeader);
    dialogContent.appendChild(dialogText);
    dialogContent.appendChild(addMoreBtn);
    dialogContent.appendChild(finalizeBtn);
    dialogOverlay.appendChild(dialogContent);
    document.body.appendChild(dialogOverlay);
    
    // Button event handlers
    addMoreBtn.addEventListener('click', () => {
        dialogOverlay.remove();
        // Trigger design upload for next design
        initiateNextDesignUpload(compositeUrl, wasBackImage);
    });
    
    finalizeBtn.addEventListener('click', () => {
        dialogOverlay.remove();
        // Continue with original flow - send message to proceed to size selection
        sendMessage();
    });
}

// New function to initiate next design upload
function initiateNextDesignUpload(previousDesignUrl, wasBackImage) {
    // Update the appropriate product image with the composite
    if (wasBackImage) {
        currentProductBackImageUrl = previousDesignUrl;
    } else {
        currentProductImageUrl = previousDesignUrl;
    }
    
    // Increment designs added counter
    designsAdded++;
    
    // Trigger the image upload input
    imageUploadButton.click();
}

// SVG-based composite renderer function
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
        
        // Store the compositeUrl for potential next design placement
        window.latestCompositeUrl = compositeUrl;
        
        // Show intermediate dialog instead of immediately sending message
        showDesignOptionsDialog(compositeUrl, showBackImage);
        
    } catch (error) {
        console.error('Error saving placement:', error);
        addMessage('Sorry, there was an error saving your design placement. Please try again.', 'system');
    }
}