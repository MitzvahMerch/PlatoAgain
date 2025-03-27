const createChatPermissionManager = () => {
    console.log('Initializing Enhanced Chat Permission Manager...');
    
    // State variables
    let chatEnabled = true;
    let disabledReason = '';
    let pendingInteractions = [];
    let activeInteractionType = null;
    
    // Cache DOM elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const uploadButton = document.querySelector('.chat-upload-button');
    
    // Setup DOM elements for permission UI
    const setupUI = () => {
        // Add the CSS styles for the permission indicator with improved styling
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Style the send button when disabled */
            #send-button.chat-disabled {
                opacity: 0.4;
                cursor: not-allowed;
                pointer-events: none;
            }
            
            /* Style the chat input when disabled */
            #chat-input.chat-disabled {
                opacity: 0.5;
                background-color: rgba(100, 100, 100, 0.2);
                cursor: not-allowed;
                pointer-events: none;
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(255, 255, 255, 0.2);
            }
            
            /* Style the upload button when disabled */
            .chat-upload-button.chat-disabled {
                opacity: 0.4;
                cursor: not-allowed;
                pointer-events: none;
            }
            
            /* Disabled chat input placeholder text */
            #chat-input.chat-disabled::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
            
            /* Create a relative positioning context for the tooltip */
            .chat-input-tooltip {
                position: fixed;
                background-color: rgba(0, 0, 0, 0.8);
                color: rgba(255, 255, 255, 0.95);
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                white-space: nowrap;
                pointer-events: none;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.2s ease;
                transform: translate(10px, -30px);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Input wrapper disabled state */
            .input-wrapper.chat-disabled {
                background-color: rgba(100, 100, 100, 0.2);
                border-color: rgba(255, 255, 255, 0.2);
            }
            
            /* Chat disabled overlay to show current state */
            .chat-disabled-overlay {
                position: absolute;
                left: 0;
                right: 0;
                top: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 5;
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: none;
                border-radius: 4px;
            }
            
            .chat-disabled-overlay.visible {
                opacity: 1;
            }
            
            .chat-disabled-message {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                max-width: 90%;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            /* Shake animation for trying to use disabled chat */
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            .shake-animation {
                animation: shake 0.4s ease-in-out;
            }
        `;
        document.head.appendChild(styleElement);
    };
    
    // Create tooltip element for cursor following
    let tooltipEl = null;
    let overlayEl = null;
    let overlayMessageEl = null;
    
    const setupTooltipAndOverlay = () => {
        // Create tooltip
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'chat-input-tooltip';
        tooltipEl.textContent = 'Please complete the action above to continue';
        document.body.appendChild(tooltipEl);
        
        // Position the tooltip near the cursor when hovering over the disabled chat input
        chatInput.addEventListener('mousemove', (e) => {
            if (!chatEnabled) {
                tooltipEl.style.left = `${e.clientX}px`;
                tooltipEl.style.top = `${e.clientY}px`;
                tooltipEl.style.opacity = '1';
                
                // Update tooltip text based on current disabled reason
                tooltipEl.textContent = disabledReason;
            }
        });
        
        chatInput.addEventListener('mouseleave', () => {
            tooltipEl.style.opacity = '0';
        });
        
        // Create overlay for input wrapper
        const inputWrapper = document.querySelector('.input-wrapper');
        if (inputWrapper) {
            // Create the overlay and message elements
            overlayEl = document.createElement('div');
            overlayEl.className = 'chat-disabled-overlay';
            
            overlayMessageEl = document.createElement('div');
            overlayMessageEl.className = 'chat-disabled-message';
            overlayMessageEl.textContent = 'Please make a selection above to continue';
            
            overlayEl.appendChild(overlayMessageEl);
            inputWrapper.appendChild(overlayEl);
            
            // Set position to relative if not already
            if (window.getComputedStyle(inputWrapper).position !== 'relative') {
                inputWrapper.style.position = 'relative';
            }
        }
    };
    
    // Update the UI based on permission state
    const updateUI = () => {
        if (!sendButton || !chatInput) return;
        
        const inputWrapper = document.querySelector('.input-wrapper');
        
        if (!chatEnabled) {
            // Disable chat input and related elements
            sendButton.classList.add('chat-disabled');
            chatInput.classList.add('chat-disabled');
            
            if (uploadButton) {
                uploadButton.classList.add('chat-disabled');
            }
            
            if (inputWrapper) {
                inputWrapper.classList.add('chat-disabled');
            }
            
            // Update overlay message and show it
            if (overlayMessageEl) {
                overlayMessageEl.textContent = disabledReason;
            }
            
            if (overlayEl) {
                overlayEl.classList.add('visible');
            }
            
            // Change placeholder text to indicate disabled state
            const originalPlaceholder = chatInput.getAttribute('data-original-placeholder') || chatInput.placeholder;
            if (!chatInput.getAttribute('data-original-placeholder')) {
                chatInput.setAttribute('data-original-placeholder', originalPlaceholder);
            }
            
            chatInput.placeholder = 'Complete the action above to continue...';
        } else {
            // Enable chat input and related elements
            sendButton.classList.remove('chat-disabled');
            chatInput.classList.remove('chat-disabled');
            
            if (uploadButton) {
                uploadButton.classList.remove('chat-disabled');
            }
            
            if (inputWrapper) {
                inputWrapper.classList.remove('chat-disabled');
            }
            
            // Hide overlay
            if (overlayEl) {
                overlayEl.classList.remove('visible');
            }
            
            // Reset tooltip
            if (tooltipEl) {
                tooltipEl.style.opacity = '0';
            }
            
            // Restore original placeholder
            const originalPlaceholder = chatInput.getAttribute('data-original-placeholder');
            if (originalPlaceholder) {
                chatInput.placeholder = originalPlaceholder;
            }
        }
        
        // Update tooltip text
        if (tooltipEl) {
            tooltipEl.textContent = disabledReason;
        }
    };
    
    // Disable chat sending with a reason
    const disableChat = (reason, interactionType) => {
        chatEnabled = false;
        disabledReason = reason || 'Please complete the action above to continue';
        
        // Update the active interaction type
        activeInteractionType = interactionType || 'unknown';
        
        updateUI();
        
        // Log the chat disable event
        console.log(`Chat disabled due to: ${reason} (${activeInteractionType})`);
    };
    
    // Enable chat sending
    const enableChat = () => {
        chatEnabled = true;
        disabledReason = '';
        activeInteractionType = null;
        
        updateUI();
        
        // Log the chat enable event
        console.log('Chat enabled');
    };
    
    // Override the sendMessage function to check permissions
    const overrideSendMessage = () => {
        // Store the original sendMessage function
        const originalSendMessage = window.sendMessage;
        
        // Replace with our permission-aware version
        window.sendMessage = function() {
            if (!chatEnabled) {
                // Visual feedback - shake the input wrapper
                const inputWrapper = document.querySelector('.input-wrapper');
                if (inputWrapper) {
                    inputWrapper.classList.add('shake-animation');
                    
                    // Remove the class after animation completes
                    setTimeout(() => {
                        inputWrapper.classList.remove('shake-animation');
                    }, 500);
                }
                
                // Show tooltip clearly
                if (tooltipEl) {
                    const rect = chatInput.getBoundingClientRect();
                    tooltipEl.style.left = `${rect.left + rect.width / 2}px`;
                    tooltipEl.style.top = `${rect.top - 40}px`;
                    tooltipEl.style.opacity = '1';
                    tooltipEl.style.transform = 'translate(-50%, 0)'; // Center horizontally
                    
                    // Hide after a moment
                    setTimeout(() => {
                        tooltipEl.style.opacity = '0';
                        tooltipEl.style.transform = 'translate(10px, -30px)'; // Reset position
                    }, 2000);
                }
                
                return false;
            }
            
            // If chat is enabled, call the original function
            return originalSendMessage.apply(this, arguments);
        };
    };
    
    // Register an interactive component that will disable chat while active
    const registerInteraction = (componentName, options = {}) => {
        // Create an interaction object with metadata
        const interaction = {
            name: componentName,
            type: options.type || 'default',
            disableMessage: options.disableMessage || `Please complete the ${componentName} to continue`,
            timestamp: Date.now()
        };
        
        // Add the component to the pending interactions list
        pendingInteractions.push(interaction);
        
        // If this is the first component added, disable chat
        if (pendingInteractions.length === 1) {
            disableChat(interaction.disableMessage, interaction.type);
        }
        
        // Log registration
        console.log(`Registered interaction: ${componentName} (${interaction.type})`);
        
        return interaction;
    };
    
    // Mark a component's interaction as completed
    const markInteractionComplete = (componentName) => {
        // Log before removing
        const interaction = pendingInteractions.find(i => i.name === componentName);
        if (interaction) {
            console.log(`Completing interaction: ${componentName} (${interaction.type})`);
        }
        
        // Remove the component from the pending list
        pendingInteractions = pendingInteractions.filter(i => i.name !== componentName);
        
        // If no more pending interactions, enable chat
        if (pendingInteractions.length === 0) {
            enableChat();
        } else {
            // Otherwise update with the next component's message
            disableChat(
                pendingInteractions[0].disableMessage,
                pendingInteractions[0].type
            );
        }
    };
    
    // Special handler for upload button click
    const handleUploadButtonClick = () => {
        // When upload button is clicked, we'll create a flag to track completion
        window.uploadRequiresCompletion = true;
        
        // Register this as an interaction
        registerInteraction('uploadDesign', {
            type: 'upload',
            disableMessage: 'Please complete the design upload process'
        });
        
        // Override the existing image upload change handler temporarily
        const imageUpload = document.getElementById('image-upload');
        const originalOnChange = imageUpload.onchange;
        
        imageUpload.onchange = function(e) {
            // Only mark as complete if a file is actually selected
            if (e.target.files && e.target.files.length > 0) {
                window.uploadRequiresCompletion = false;
                
                // Note: Don't mark as complete yet - there's a multi-step process
                // The final confirmation will happen in:
                // - svgBasedCompositeRenderer function (when design placement completes)
                // - or if upload fails/is cancelled
            }
            
            // Call the original handler
            if (typeof originalOnChange === 'function') {
                originalOnChange.call(this, e);
            }
            
            // Reset the onchange to the original after it fires once
            setTimeout(() => {
                imageUpload.onchange = originalOnChange;
            }, 100);
        };
    };
    
    // Function to actively scan the chat for UI elements that should disable chat input
    const scanChatForInteractiveElements = () => {
        // Scan for product buttons
        const productButtonsContainers = document.querySelectorAll('.product-buttons-container');
        if (productButtonsContainers.length > 0 && pendingInteractions.length === 0) {
            registerInteraction('productSelection', {
                type: 'buttons',
                disableMessage: 'Please select a product option to continue'
            });
        }
        
        // Scan for design options
        const designOptionsContainers = document.querySelectorAll('.design-options-container');
        if (designOptionsContainers.length > 0 && pendingInteractions.length === 0) {
            registerInteraction('designOptions', {
                type: 'buttons',
                disableMessage: 'Please select a design option to continue'
            });
        }
        
        // Scan for quantity selectors
        const quantitySelectors = document.querySelectorAll('.quantity-selector-container');
        if (quantitySelectors.length > 0 && pendingInteractions.length === 0) {
            registerInteraction('quantitySelection', {
                type: 'form',
                disableMessage: 'Please enter your order quantities to continue'
            });
        }
        
        // Scan for shipping forms
        const shippingForms = document.querySelectorAll('.shipping-form-container');
        if (shippingForms.length > 0 && pendingInteractions.length === 0) {
            registerInteraction('shippingForm', {
                type: 'form',
                disableMessage: 'Please complete the shipping form to continue'
            });
        }
    };
    
    // Add MutationObserver to automatically detect and register UI components
    const setupAutoDetection = () => {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        // Create observer to watch for new interactive elements
        const observer = new MutationObserver(mutations => {
            let shouldScan = false;
            
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if any added nodes might contain interactive elements
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // If this is a message that might contain interactive elements
                            if (node.classList && node.classList.contains('message')) {
                                shouldScan = true;
                            }
                            // If this node itself is an interactive element
                            else if (
                                node.classList && (
                                    node.classList.contains('product-buttons-container') ||
                                    node.classList.contains('design-options-container') ||
                                    node.classList.contains('quantity-selector-container') ||
                                    node.classList.contains('shipping-form-container')
                                )
                            ) {
                                shouldScan = true;
                            }
                        }
                    });
                }
            });
            
            // Perform scan if needed, with a short delay to allow DOM to settle
            if (shouldScan) {
                setTimeout(scanChatForInteractiveElements, 100);
            }
        });
        
        // Start observing
        observer.observe(chatMessages, { childList: true, subtree: true });
        return observer;
    };
    
    // Function to get currently active elements for debugging
    const getActiveInteractions = () => {
        return {
            chatEnabled,
            disabledReason,
            activeInteractionType,
            pendingInteractions: [...pendingInteractions]
        };
    };
    
    // Initialize the manager
    const init = () => {
        setupUI();
        setupTooltipAndOverlay();
        overrideSendMessage();
        
        // Initial UI state - enabled by default
        enableChat();
        
        // Setup automatic detection of interactive elements
        const observer = setupAutoDetection();
        
        // Perform initial scan
        setTimeout(scanChatForInteractiveElements, 500);
        
        return observer;
    };
    
    // Initialize
    const observer = init();
    
    // Return public API
    return {
        disableChat,
        enableChat,
        registerInteraction,
        markInteractionComplete: markInteractionComplete,
        handleUploadButtonClick,
        isChatEnabled: () => chatEnabled,
        getActiveInteractions,
        scanForInteractiveElements: scanChatForInteractiveElements,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

// Initialize and export
window.chatPermissions = createChatPermissionManager();
console.log('Enhanced Chat Permission Manager created and assigned to window.chatPermissions');

// Patch known integration points to ensure they work with the new permissions system

// Patch design placer callback to mark interaction complete
const originalSvgBasedCompositeRenderer = window.svgBasedCompositeRenderer;
if (typeof originalSvgBasedCompositeRenderer === 'function') {
    window.svgBasedCompositeRenderer = async function(placement) {
        try {
            // Call the original renderer
            await originalSvgBasedCompositeRenderer(placement);
            
            // Mark the upload interaction as complete
            if (window.chatPermissions) {
                window.chatPermissions.markInteractionComplete('uploadDesign');
            }
            
            // If there's a callback for successful placement, call it
            if (typeof window.onDesignPlacementSaved === 'function') {
                window.onDesignPlacementSaved();
            }
        } catch (error) {
            console.error('Error in patched svgBasedCompositeRenderer:', error);
            
            // Even on error, mark as complete to avoid locking the UI
            if (window.chatPermissions) {
                window.chatPermissions.markInteractionComplete('uploadDesign');
            }
            
            // Re-throw to maintain original error handling
            throw error;
        }
    };
    console.log('Patched svgBasedCompositeRenderer for chat permissions integration');
}

// Patch modalplacement.hide to cancel upload process if needed
let originalPlacementModalHide = null;
document.addEventListener('DOMContentLoaded', () => {
    if (window.placementModal && typeof window.placementModal.hide === 'function') {
        originalPlacementModalHide = window.placementModal.hide;
        
        window.placementModal.hide = function() {
            // If this wasn't marked as saved by the confirmSave method, treat as cancelled
            if (!window.placementModal._saveConfirmed && window.chatPermissions) {
                console.log('Design placement cancelled, re-enabling chat');
                window.chatPermissions.markInteractionComplete('uploadDesign');
            }
            
            // Reset the flag
            window.placementModal._saveConfirmed = false;
            
            // Call original
            return originalPlacementModalHide.apply(this, arguments);
        };
        
        // Add method to confirm save happened
        window.placementModal.confirmSave = function() {
            window.placementModal._saveConfirmed = true;
        };
        
        console.log('Patched placementModal.hide for chat permissions integration');
    }
});

// Re-scan for interactive elements when window loads and after short delay
window.addEventListener('load', () => {
    if (window.chatPermissions) {
        window.chatPermissions.scanForInteractiveElements();
        
        // Scan again after a moment in case components load asynchronously
        setTimeout(() => {
            window.chatPermissions.scanForInteractiveElements();
        }, 1000);
    }
});