const createDesignOptionsIntegration = () => {
    console.log('Initializing Design Options Chat Integration...');

    // Add the CSS styles for the design options integration
    const addStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .design-options-container {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                width: 100%;
            }
            
            .design-options-header {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 15px;
                text-align: center;
            }
            
            .design-options-text {
                margin-bottom: 15px;
                color: white;
                text-align: center;
            }
            
            .logo-charge-notice {
                font-size: 14px;
                color: #ffcc00;
                margin-bottom: 15px;
                text-align: center;
            }
            
            .design-options-buttons {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 15px;
            }
            
            .design-option-btn {
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .add-design-btn {
                background-color: var(--primary-color);
                color: white;
            }
            
            .add-design-btn:hover {
                background-color: var(--primary-color-dark);
            }
            
            .finalize-btn {
                background-color: #4CAF50;
                color: white;
            }
            
            .finalize-btn:hover {
                background-color: #3d9840;
            }
        `;
        
        document.head.appendChild(styleElement);
    };

    // Store a reference to the active design options container
    let activeContainer = null;

    // Function to inject design options directly into chat message
    const injectDesignOptions = (messageElement, compositeUrl, wasBackImage) => {
        console.log('Injecting design options into chat message');
        
        // Don't inject if already done
        if (messageElement.querySelector('.design-options-container')) {
            console.log('Design options already injected, skipping');
            return;
        }
        
        // Create the container
        const container = document.createElement('div');
        container.className = 'design-options-container';
        if (window.chatPermissions) {
            window.chatPermissions.registerButtonComponent('designOptions', {
                disableMessage: 'Please choose whether to add another design or finalize your customization'
            });
        }
        
        // Create header
        const header = document.createElement('div');
        header.className = 'design-options-header';
        header.textContent = 'Design Added Successfully!';
        container.appendChild(header);
        
        // Add logo charge notification
        const chargeNotice = document.createElement('div');
        chargeNotice.className = 'logo-charge-notice';
        chargeNotice.textContent = 'A $1.50 charge per item has been added for this logo.';
        container.appendChild(chargeNotice);
        
        // Add explanatory text
        const text = document.createElement('div');
        text.className = 'design-options-text';
        text.textContent = 'What would you like to do next?';
        container.appendChild(text);
        
        // Create buttons container
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'design-options-buttons';
        
        // Add another design button
        const addMoreBtn = document.createElement('button');
        addMoreBtn.textContent = 'Add Another Design';
        addMoreBtn.className = 'design-option-btn add-design-btn';
        
        // Finalize button
        const finalizeBtn = document.createElement('button');
        finalizeBtn.textContent = 'Finalize Customization';
        finalizeBtn.className = 'design-option-btn finalize-btn';
        
        // Add buttons to container
        buttonsContainer.appendChild(addMoreBtn);
        buttonsContainer.appendChild(finalizeBtn);
        container.appendChild(buttonsContainer);
        
        // Add the container to the message
        messageElement.appendChild(container);
        
        // Save reference to the active container
        activeContainer = container;
        
        // Button event handlers (same as the original showDesignOptionsDialog function)
        addMoreBtn.addEventListener('click', () => {
            // Mark this component as selected
            if (window.chatPermissions) {
                window.chatPermissions.markButtonSelected('designOptions');
            }
            
            // FIXED: Don't hide the options yet - we'll only hide them after a successful placement
            // container.style.display = 'none';
            
            // Store a reference to the placement modal
            const origModalOnHide = window.placementModal.onHide;
            
            // Override the onHide method to detect if the placement was canceled
            window.placementModal.onHide = () => {
                // Restore the original onHide handler
                window.placementModal.onHide = origModalOnHide;
                
                // If there's a save in progress, the original event will handle this
                // Don't do anything here - let the design placer's save button handle it
                if (origModalOnHide) origModalOnHide();
            };
            
            // Register a callback that will be called when the design is successfully placed
            window.onDesignPlacementSaved = () => {
                // Once design is successfully placed, hide the options
                container.style.display = 'none';
                
                // Clean up the callback to avoid memory leaks
                window.onDesignPlacementSaved = null;
            };
            
            // Call the existing function to initiate next design upload
            initiateNextDesignUpload(compositeUrl, wasBackImage);
        });
        
        finalizeBtn.addEventListener('click', () => {
            // Mark this component as selected
            if (window.chatPermissions) {
                window.chatPermissions.markButtonSelected('designOptions');
            }
            
            // Hide the options after selection to avoid confusion
            container.style.display = 'none';
            
            // Add a confirmation message in the chat
            addMessage("Design Finalized!", 'system');
            
            // Continue with original flow - send message to proceed to size selection
            sendMessage();
        });
    };

    // Add the message handler function for the bot response
    const handleBotMessage = (messageElement, designData) => {
        // Check if this is a design upload confirmation message
        if (messageElement.textContent.includes('Design placement preview')) {
            // Create a small delay to ensure this runs after the image is added
            setTimeout(() => {
                // Get the latest composite URL from window
                const compositeUrl = window.latestCompositeUrl;
                const wasBackImage = false; // Default to front image if not specified
                
                // Inject the design options
                injectDesignOptions(messageElement, compositeUrl, wasBackImage);
            }, 100);
        }
    };

    // Observer to watch for new messages
    const observeMessages = () => {
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
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // If this is a product image (containing the design preview)
                            if (node.classList.contains('product-image')) {
                                const imgElement = node.querySelector('img');
                                if (imgElement && imgElement.alt === 'Design placement preview') {
                                    // Get the bot message that came before this image
                                    const prevSibling = node.previousElementSibling;
                                    if (prevSibling && prevSibling.classList.contains('message') && prevSibling.classList.contains('bot')) {
                                        // Now inject the design options into this message
                                        const compositeUrl = imgElement.src;
                                        const wasBackImage = false; // Default to front image if not specified
                                        injectDesignOptions(prevSibling, compositeUrl, wasBackImage);
                                    }
                                }
                            }
                        }
                    });
                }
            });
        });
        
        // Start observing
        observer.observe(chatMessages, { childList: true, subtree: true });
        
        return observer;
    };

    // Initialize
    addStyles();
    const observer = observeMessages();
    
    // Return public API
    return {
        injectIntoMessage: injectDesignOptions,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

// Initialize and export the design options integration
window.designOptionsIntegration = createDesignOptionsIntegration();
console.log('Design Options integration created and assigned to window.designOptionsIntegration');