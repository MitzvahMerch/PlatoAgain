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

// Function to inject counters into the first message
function injectCountersIntoFirstMessage() {
    // Find the first bot message
    const firstBotMessage = document.querySelector('#chat-messages .message.bot:first-child');
  
    if (!firstBotMessage) {
      console.error('First bot message not found');
      return;
    }
    
    // Check if counter is already added to avoid duplicates
    if (firstBotMessage.querySelector('.plato-stats-card')) {
      console.log('Counter already exists, not adding again');
      return;
    }
  
    // Create main container with card-like appearance
    const statsCard = document.createElement('div');
    statsCard.className = 'plato-stats-card';
    statsCard.style.cssText = `
      margin: 15px auto;
      padding: 16px;
      background-color: #121212;
      border-radius: 10px;
      border-left: 4px solid #E08442;
      width: 100%;
      max-width: 600px;
      box-sizing: border-box;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    `;
  
    // Create header with trust indicators
    const cardHeader = document.createElement('div');
    cardHeader.style.cssText = `
      display: flex;
      align-items: center;
      margin-bottom: 15px;
      justify-content: space-between;
    `;
  
    // Create the badge icon and text
    const badgeContainer = document.createElement('div');
    badgeContainer.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
    `;
  
    // SVG for verified badge
    const verifiedIcon = document.createElement('div');
    verifiedIcon.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#E08442" />
      </svg>
    `;
  
    // Label for verified status
    const verifiedLabel = document.createElement('div');
    verifiedLabel.textContent = "Verified Bulk Printer";
    verifiedLabel.style.cssText = `
      font-weight: bold;
      color: #E08442;
      font-size: 14px;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    `;
  
    badgeContainer.appendChild(verifiedIcon);
    badgeContainer.appendChild(verifiedLabel);
  
    // Create "Platos Pillars" label
    const statsLabel = document.createElement('div');
    statsLabel.textContent = "Platos Pillars";
    statsLabel.style.cssText = `
      color: #888888;
      font-size: 16px;
      font-weight: bold;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    `;
  
    // Add elements to header
    cardHeader.appendChild(badgeContainer);
    cardHeader.appendChild(statsLabel);
    statsCard.appendChild(cardHeader);
  
    // Create the counters container
    const countersContainer = document.createElement('div');
    countersContainer.className = 'plato-counters-container';
    countersContainer.style.cssText = `
      width: 100%;
      box-sizing: border-box;
      display: flex;
      justify-content: flex-start;
      gap: 20px;
      margin-top: 10px;
    `;
  
    // Calculate the counter value for Orders Completed
    const startDate = new Date('2025-01-01');
    const today = new Date();
    const daysSinceStart = Math.floor((today - startDate) / (24 * 60 * 60 * 1000));
    const ordersCompleted = 68 + daysSinceStart;
  
    // Create Orders Completed counter
    const ordersCounter = createCounter(
      ordersCompleted, 
      'Orders Completed', 
      'Trusted by businesses nationwide'
    );
  
    // Create the "Order Minimum" counter
    const bulkCounter = createCounter(
      '24 Units', 
      'Order Minimum', 
      'Bulk pricing for quality prints'
    );
  
    // Add the counters to the container
    countersContainer.appendChild(ordersCounter);
    countersContainer.appendChild(bulkCounter);
  
    // Add the counters container to the stats card
    statsCard.appendChild(countersContainer);
  
    // Create a small trust banner at the bottom
    const trustBanner = document.createElement('div');
    trustBanner.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 20px;
      padding-top: 15px;
      border-top: 1px solid #333333;
      font-size: 12px;
      color: #888888;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    `;
  
    // Small lock icon for security
    const lockIcon = document.createElement('div');
    lockIcon.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 11H5V21H19V11Z" fill="#666" />
        <path d="M17 11V8C17 5.24 14.76 3 12 3C9.24 3 7 5.24 7 8V11" stroke="#666" fill="none" />
      </svg>
    `;
  
    // Trust text
    const trustText = document.createElement('span');
    trustText.textContent = "Secure Payments • Chat Interface • 100% Satisfaction Guarantee";
  
    trustBanner.appendChild(lockIcon);
    trustBanner.appendChild(trustText);
    statsCard.appendChild(trustBanner);
  
    // Insert the entire stats card right after the text content of the first message
    firstBotMessage.appendChild(statsCard);
  
    // Helper function to create counter elements
    function createCounter(value, label, subtext) {
      const counter = document.createElement('div');
      counter.className = 'plato-counter';
      counter.style.cssText = `
        flex: 1;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
      `;
  
      const counterValue = document.createElement('div');
      counterValue.className = 'counter-value';
      counterValue.textContent = value;
      counterValue.style.cssText = `
        background-color: #E08442;
        color: white;
        font-size: 22px;
        font-weight: bold;
        padding: 8px 12px;
        border-radius: 8px;
        width: 120px;
        text-align: center;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(224, 132, 66, 0.3);
        transition: transform 0.2s ease;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      `;
  
      // Add hover effect
      counterValue.onmouseover = function() {
        this.style.transform = 'scale(1.05)';
      };
      counterValue.onmouseout = function() {
        this.style.transform = 'scale(1)';
      };
  
      const counterLabel = document.createElement('div');
      counterLabel.className = 'counter-label';
      counterLabel.textContent = label;
      counterLabel.style.cssText = `
        color: #888888;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 4px;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      `;
  
      const counterSubtext = document.createElement('div');
      counterSubtext.className = 'counter-subtext';
      counterSubtext.textContent = subtext;
      counterSubtext.style.cssText = `
        color: #666666;
        font-size: 12px;
        max-width: 150px;
        text-align: center;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      `;
  
      counter.appendChild(counterValue);
      counter.appendChild(counterLabel);
      counter.appendChild(counterSubtext);
  
      return counter;
    }
}
  
// Generate a random user ID for this session
let userId;
  
// Function to generate a new user ID
function generateNewUserId() {
    // Use current timestamp plus random string for better uniqueness
    const timestamp = Date.now().toString(36);
    const randomStr = Math.random().toString(36).substr(2, 9);
    return 'user_' + timestamp + randomStr;
}
  
// Check if we need a new user ID when page loads
window.addEventListener('DOMContentLoaded', () => {
    // Always generate a brand new user ID on page load/reload
    userId = generateNewUserId();
    console.log('New conversation started with user ID:', userId);
      
    // Call the function to adjust chat container height for mobile
    adjustChatContainerHeight();
      
    // Set up keyboard visibility detection
    handleKeyboardVisibility();
});
  
const API_BASE_URL = 'https://platosprints-5w8mn.ondigitalocean.app';
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
            addMessage("Hey! I'm Plato. Let's finalize your bulk custom clothing order right now!", 'bot');
            // Inject counters AFTER the first welcome message is appended
            setTimeout(() => {
                injectCountersIntoFirstMessage();
            }, 100);
              
            addMessage("What type of clothing, and in what color, are you looking to customize today?", 'bot');
        } else {
            addMessage("Warning: System is currently unavailable. Please try again later.", 'system');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        addMessage("Warning: Unable to connect to the server. Please make sure the backend is running.", 'system');
    }
});
  
// Add a function to reset the conversation with a new user ID
window.resetConversation = function() {
    // Generate a new user ID
    userId = generateNewUserId();
      
    // Clear chat messages
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
      
    // Add initial welcome message
    addMessage("Hey! I'm Plato. Let's finalize your bulk custom clothing order right now!", 'bot');
    // Inject counters after reset
    setTimeout(() => {
        injectCountersIntoFirstMessage();
    }, 100);
      
    addMessage("What type of clothing, and in what color, are you looking to customize today?", 'bot');
      
    console.log('Conversation reset with new user ID:', userId);
};
  
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
    chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px'; // Limit max height
});
  
// Handle input focus to prevent interface issues on mobile
chatInput.addEventListener('focus', () => {
    // On mobile, scroll to ensure the input is visible when focused
    if (window.innerWidth <= 600) {
        // Add class to body to indicate keyboard is visible
        document.body.classList.add('keyboard-visible');
          
        // Wait a moment for the keyboard to appear
        setTimeout(() => {
            // Scroll the chat area to show recent messages
            chatMessages.scrollTop = chatMessages.scrollHeight;
            // Adjust the chat container height
            adjustChatContainerHeight();
        }, 300);
    }
});
  
chatInput.addEventListener('blur', () => {
    // On mobile, handle keyboard hiding
    if (window.innerWidth <= 600) {
        // Remove class from body to indicate keyboard is hidden
        document.body.classList.remove('keyboard-visible');
          
        // Adjust container height after keyboard hides
        setTimeout(() => {
            adjustChatContainerHeight();
        }, 100);
    }
});
  
// Image upload handling with background removal and design placement
imageUploadButton.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
  
    try {
        // Store file and update UI
        window.currentUpload = file;
        const uploadButton = document.querySelector('.chat-upload-button svg');
        uploadButton.innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
        uploadButton.style.color = 'var(--success-color)';
          
        // Create temporary URL for the uploaded file
        const tempImageUrl = URL.createObjectURL(file);
          
        // Show background removal modal first
        window.backgroundRemovalModal.show(tempImageUrl, file, async (result) => {
            if (!result.success) {
                throw new Error(result.error || 'Failed to process image');
            }
              
            // Upload the processed file to Firebase
            const uploadResult = await window.uploadDesignImage(result.processedFile || file, userId);
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
        });
          
    } catch (error) {
        console.error('Error processing image:', error);
        addMessage('Sorry, there was an error processing your image. Please try again.', 'system');
          
        // Reset the file input and button
        const fileInput = document.getElementById('image-upload');
        if (fileInput) fileInput.value = '';
          
        const uploadButton = document.querySelector('.chat-upload-button svg');
        if (uploadButton) {
            uploadButton.innerHTML = `
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
            `;
            uploadButton.style.color = 'var(--secondary-color)';
        }
    }
});
  
async function sendMessage() {
    // Check if there's an incomplete upload
    if (!userId) {
        userId = generateNewUserId();
        console.warn('User ID was missing, generated new ID:', userId);
    }
      
    if (window.uploadRequiresCompletion === true) {
        // User tried to send message without completing upload
        return;
    }
      
    const message = chatInput.value.trim();
    const hasImage = window.currentUpload;
      
    if (!message && !hasImage) return;
  
    if (message) {
        addMessage(message, 'user');
          
        // Track first message sent with Google Ads
        if (!window.googleAdsTracking?.firstMessageSent) {
            console.log('Tracking first message conversion event');
            gtag('event', 'conversion', {
                'send_to': 'AW-16970928099/w1iyCKmP_LQaEOOfr5w_',
                'value': 1.0, // Assigning a $0.50 value to starting a conversation
                'currency': 'USD',
                'transaction_id': `msg_${Date.now()}_${userId}`
            });
              
            // Mark as tracked to prevent duplicate events
            if (!window.googleAdsTracking) window.googleAdsTracking = {};
            window.googleAdsTracking.firstMessageSent = true;
        }
    }
  
    chatInput.value = '';
    chatInput.style.height = 'auto';
      
    // Hide keyboard after sending on mobile
    if (window.innerWidth <= 600) {
        chatInput.blur();
    }
      
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
                const imageUrl = `${API_BASE_URL}/api${image.url}`;
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
      
    // Removed the code that injected counters here (to prevent duplication)
      
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
  
function showDesignOptionsDialog(compositeUrl, wasBackImage) {
    // Store the compositeUrl for potential next design placement
    window.latestCompositeUrl = compositeUrl;
      
    // Create a bot message specifically for our design options
    const optionsMessage = addMessage("Design added successfully! What would you like to do next?", 'bot');
      
    // Now we have a bot message, we can safely inject our options
    if (window.designOptionsIntegration && typeof window.designOptionsIntegration.injectIntoMessage === 'function') {
        window.designOptionsIntegration.injectIntoMessage(optionsMessage, compositeUrl, wasBackImage);
    } else {
        console.error('Design options integration not available');
        // Fallback to original behavior if integration is missing
        sendMessage();
    }
}
  
// New function to initiate next design upload
function initiateNextDesignUpload(previousDesignUrl, wasBackImage) {
    // Update the appropriate product image with the composite
    if (wasBackImage) {
        currentProductBackImageUrl = previousDesignUrl;
    } else {
        currentProductImageUrl = previousDesignUrl;
    }
      
    // Increment designsAdded counter
    designsAdded++;
      
    // Trigger the image upload input
    imageUploadButton.click();
}
  
// SVG-based composite renderer function (modified for bug fix)
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
          
        // ADDED: Let the modal know this was saved, not cancelled
        if (window.placementModal && typeof window.placementModal.confirmSave === 'function') {
            window.placementModal.confirmSave();
        }
          
        // Close modal and show result
        window.placementModal.hide();
        addProductImage(compositeUrl, 'Design placement preview');
          
        // Track logo upload event for Google Ads
        if (!window.googleAdsTracking?.logoUploaded) {
            console.log('Tracking logo upload conversion event');
            gtag('event', 'conversion', {
                'send_to': 'AW-16970928099/aT3KCKGI77QaEOOfr5w_',
                'value': 1.0, // Assigning a $1 value to uploading a logo
                'currency': 'USD',
                'transaction_id': `logo_${Date.now()}_${userId}`
            });
              
            // Mark as tracked to prevent duplicate events
            if (!window.googleAdsTracking) window.googleAdsTracking = {};
            window.googleAdsTracking.logoUploaded = true;
        }
          
        // NEW CODE: Explicitly tell the backend about the logo upload
        try {
            console.log('Updating backend with logo information...');
            const response = await fetch(`${API_BASE_URL}/api/update-design`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    design_url: compositeUrl,
                    filename: compositeFileName,
                    has_logo: true  // This is the key - explicitly telling backend this has a logo
                }),
            });
              
            if (!response.ok) {
                console.warn('Warning: Failed to update design with logo information', await response.text());
            } else {
                console.log('Successfully updated backend with logo information');
                  
                // Add message about the logo charge
                addMessage("A $1.50 charge per item has been added for this logo.", 'system');
            }
        } catch (error) {
            console.warn('Error updating logo information:', error);
            // Continue despite this error - we'll just show the design
        }
          
        // Store the compositeUrl for potential next design placement
        window.latestCompositeUrl = compositeUrl;
          
        // Show intermediate dialog instead of immediately sending message
        showDesignOptionsDialog(compositeUrl, showBackImage);
          
    } catch (error) {
        console.error('Error saving placement:', error);
        addMessage('Sorry, there was an error saving your design placement. Please try again.', 'system');
    }
}
  
// Detect keyboard visibility on mobile
function handleKeyboardVisibility() {
    // iOS-specific keyboard detection
    if (window.innerWidth <= 600) {
        // This detects when an input is focused
        document.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('focus', () => {
                document.body.classList.add('keyboard-visible');
                  
                // Scroll the chat container to show the input area
                setTimeout(() => {
                    const chatFooter = document.querySelector('.chat-footer');
                    if (chatFooter) {
                        chatFooter.scrollIntoView(false);
                    }
                }, 100);
            });
              
            input.addEventListener('blur', () => {
                document.body.classList.remove('keyboard-visible');
                  
                // Reset the chat container
                setTimeout(() => {
                    adjustChatContainerHeight();
                }, 100);
            });
        });
          
        // Additional iOS-specific workaround
        window.addEventListener('resize', () => {
            // On iOS, window resize is triggered when keyboard appears/disappears
            const isKeyboardVisible = (window.innerHeight < window.outerHeight * 0.8);
              
            if (isKeyboardVisible) {
                document.body.classList.add('keyboard-visible');
            } else {
                document.body.classList.remove('keyboard-visible');
            }
              
            // Adjust the chat container height
            adjustChatContainerHeight();
        });
    }
}
  
// Handle window resize to adjust chat message container height
window.addEventListener('resize', () => {
    adjustChatContainerHeight();
});
  
// Function to adjust the chat container height based on viewport
function adjustChatContainerHeight() {
    if (window.innerWidth <= 600) {
        const chatMessages = document.getElementById('chat-messages');
        const header = document.querySelector('.chat-header');
        const footer = document.querySelector('.chat-footer');
          
        if (chatMessages && header && footer) {
            const headerHeight = header.offsetHeight;
            const footerHeight = footer.offsetHeight;
            const windowHeight = window.innerHeight;
              
            // Check if keyboard is visible
            const isKeyboardVisible = document.body.classList.contains('keyboard-visible');
              
            if (isKeyboardVisible) {
                // If keyboard is visible, use a smaller height
                chatMessages.style.height = `${windowHeight - headerHeight - footerHeight - 270}px`;
            } else {
                // Normal height when keyboard is not visible
                chatMessages.style.height = `${windowHeight - headerHeight - footerHeight - 20}px`;
            }
        }
    }
}
  
// Fix for input focus issues on mobile
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const inputWrapper = document.querySelector('.input-wrapper');
      
    // When clicking the wrapper, focus the input
    if (inputWrapper) {
      inputWrapper.addEventListener('click', function(e) {
        chatInput.focus();
      });
    }
      
    // Ensure chatInput stays focusable
    if (chatInput) {
      chatInput.addEventListener('blur', function() {
        // Small delay to ensure we can focus again
        setTimeout(() => {
          chatInput.setAttribute('tabindex', '0');
        }, 100);
      });
    }
      
    // Prevent scrolling to black space when keyboard is visible
    chatInput.addEventListener('focus', function() {
      document.body.classList.add('keyboard-visible');
        
      // Scroll to keep input in view
      setTimeout(() => {
        const chatFooter = document.querySelector('.chat-footer');
        if (chatFooter) {
          chatFooter.scrollIntoView(false);
        }
      }, 100);
    });
      
    chatInput.addEventListener('blur', function() {
      document.body.classList.remove('keyboard-visible');
    });
});