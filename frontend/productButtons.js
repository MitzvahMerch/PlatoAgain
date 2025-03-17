// productButtons.js
// This adds interactive product selection buttons to the chat

const createProductButtons = () => {
    console.log('Initializing product selection buttons...');

    // Add the CSS styles for the product buttons container
    const addStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .product-buttons-container {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                width: 100%;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .product-button {
                padding: 12px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s, transform 0.1s;
            }
            
            .product-button:hover {
                transform: translateY(-1px);
            }
            
            .product-button:active {
                transform: translateY(1px);
            }
            
            .upload-logo-button {
                background-color: var(--primary-color);
                color: white;
            }
            
            .find-product-button {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
            }
            
            .color-options-button {
            background-color: #4a90e2;
            color: white;
            }
            
            .product-button svg {
                margin-right: 8px;
                width: 18px;
                height: 18px;
            }
        `;
        
        document.head.appendChild(styleElement);
    };

    // Function to inject the buttons into a message
    const injectProductButtons = (messageElement, productInfo) => {
        console.log('Injecting product buttons into message:', messageElement, productInfo);
        
        // Don't inject if already done
        if (messageElement.querySelector('.product-buttons-container')) {
            console.log('Product buttons already injected, skipping');
            return;
        }
        
        // Create buttons container
        const container = document.createElement('div');
        container.className = 'product-buttons-container';
        if (window.chatPermissions) {
            window.chatPermissions.registerButtonComponent('productSelection', {
                disableMessage: 'Please select one of the options above to continue'
            });
        }
        
        // Upload Logo button
        const uploadButton = document.createElement('button');
        uploadButton.className = 'product-button upload-logo-button';
        uploadButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
            </svg>
            Upload Logo
        `;
        
        // Find New Product button
        const findProductButton = document.createElement('button');
        findProductButton.className = 'product-button find-product-button';
        findProductButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
            </svg>
            Find Different Product
        `;
        
        // Same Product, Different Color button
        const colorOptionsButton = document.createElement('button');
        colorOptionsButton.className = 'product-button color-options-button';
        colorOptionsButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            Same Product, Different Color
        `;
        
        uploadButton.addEventListener('click', () => {
            // Handle upload button click without marking as selected yet
            if (window.chatPermissions) {
                window.chatPermissions.handleUploadButtonClick();
            }
            
            // Trigger the same action as the upload button in the chat
            document.getElementById('image-upload').click();
        });
        
        findProductButton.addEventListener('click', () => {
            // Mark this component as selected
            if (window.chatPermissions) {
                window.chatPermissions.markButtonSelected('productSelection');
            }
            
            // Extract product info for the rejection message
            let productName = 'current product';
            let productColor = '';
            
            if (productInfo) {
                productName = productInfo.name || 'product';
                productColor = productInfo.color || '';
            }
            
            // Clear any existing text in the chat input
            const chatInput = document.getElementById('chat-input');
            chatInput.value = '';
            
            // Create a message that is visible to the user but still identifiable
            // as a special command by the backend
            let message = "I'd like to see a different product option.";
            
            // If we have product info, include it in the message
            if (productName !== 'current product') {
                message = `I'd like to see a different product option. The ${productColor} ${productName} isn't quite what I'm looking for. [FIND_DIFFERENT_PRODUCT]`;
            }
            
            chatInput.value = message;
            
            // Send the message
            document.getElementById('send-button').click();
            
            // Add a visual indication that the buttons have been used
            container.style.opacity = '0.5';
            uploadButton.disabled = true;
            findProductButton.disabled = true;
            if (colorOptionsButton.parentNode === container) {
                colorOptionsButton.disabled = true;
            }
        });
        
        colorOptionsButton.addEventListener('click', () => {
            // Mark this component as selected
            if (window.chatPermissions) {
                window.chatPermissions.markButtonSelected('productSelection');
            }
            
            // Get product info for the color options request
            let productName = 'current product';
            
            if (productInfo) {
                productName = productInfo.name || 'product';
            }
            
            // Clear any existing text in the chat input
            const chatInput = document.getElementById('chat-input');
            chatInput.value = '';
            
            // Create a message that requests color options
            let message = `Show me color options for this ${productName}. [SHOW_COLOR_OPTIONS]`;
            
            chatInput.value = message;
            
            // Send the message
            document.getElementById('send-button').click();
            
            // Add a visual indication that the buttons have been used
            container.style.opacity = '0.5';
            uploadButton.disabled = true;
            findProductButton.disabled = true;
            colorOptionsButton.disabled = true;
        });
        
        // Assemble and append
        const colorWasSpecified = productInfo && (
            productInfo.colorSpecified === true || 
            (productInfo.color && productInfo.colorSpecified !== false)
        );
        
        // Assemble and append in the desired order
        container.appendChild(uploadButton);
        
        // Add color options button in the middle (if it's needed)
        if (!colorWasSpecified) {
            container.appendChild(colorOptionsButton);
        }
        
        // Add find product button last
        container.appendChild(findProductButton);
        
        messageElement.appendChild(container);
    };

    // Monitor for messages that include product selection
    const observeMessages = () => {
        console.log('Starting to observe chat messages for product selection');
        
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        // Create a MutationObserver to watch for new messages
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE && 
                            node.classList.contains('message') && 
                            node.classList.contains('bot')) {
                            
                            // Check if this message includes a product selection action
                            if (node.dataset && node.dataset.action) {
                                try {
                                    const actionData = JSON.parse(node.dataset.action);
                                    if (actionData.type === 'showProductOptions' && actionData.productInfo) {
                                        console.log('Product selection detected, injecting buttons');
                                        injectProductButtons(node, actionData.productInfo);
                                    }
                                } catch (e) {
                                    console.error('Error parsing action data:', e);
                                }
                            }
                            
                            // Also check message content for product selection indicators
                            const messageText = node.textContent.toLowerCase();
                            if ((messageText.includes('found the perfect') || 
                                 messageText.includes('price of $')) && 
                                (messageText.includes('t-shirt') || 
                                 messageText.includes('jersey') || 
                                 messageText.includes('hoodie') ||
                                 messageText.includes('garment') ||
                                 messageText.includes('shirt'))) {
                                
                                // Try to extract basic product info from the message if possible
                                const productInfo = extractProductInfo(node.textContent);
                                console.log('Product selection detected in message content:', productInfo);
                                injectProductButtons(node, productInfo);
                            }
                        }
                    });
                }
            });
        });
        
        // Helper function to extract product info from message text
        const extractProductInfo = (text) => {
            const productInfo = {};
            
            // Try to extract product name
            const productNameMatch = text.match(/perfect ([^-]+)/) || 
                                    text.match(/found the ([^-]+)/);
            if (productNameMatch) {
                productInfo.name = productNameMatch[1].trim();
            }
            
            // Try to extract price
            const priceMatch = text.match(/\$(\d+\.\d+)/);
            if (priceMatch) {
                productInfo.price = priceMatch[1];
            }
            
            // Try to extract color
            const colorMatch = text.match(/in a ([a-z]+) color/) || 
                              text.match(/in ([a-z]+) color/) ||
                              text.match(/in ([a-z]+)(?= \w)/i);
            if (colorMatch) {
                productInfo.color = colorMatch[1];
                // If we found a color in the message, set colorSpecified to true
                productInfo.colorSpecified = true;
            } else {
                // No color found in the message
                productInfo.colorSpecified = false;
            }
            
            return productInfo;
        };
        
        // Start observing
        observer.observe(chatMessages, { childList: true });
        
        return observer;
    };

    // Initialize by adding styles and setting up the observer
    addStyles();
    const observer = observeMessages();
    
    // Return public API
    return {
        injectIntoMessage: injectProductButtons,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

// Initialize and export the product buttons component
console.log('Creating product selection buttons...');
window.productButtons = createProductButtons();
console.log('Product selection buttons created and assigned to window.productButtons');