const createChatPermissionManager = () => {
    console.log('Initializing Chat Permission Manager...');
    
    // State variables
    let chatEnabled = true;
    let disabledReason = '';
    let pendingButtonSelections = [];
    
    // Cache DOM elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    
    // Setup DOM elements for permission UI - MUCH SIMPLER NOW
    const setupUI = () => {
        // Add the CSS styles for the permission indicator - with chat input styles
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Style the send button when disabled */
            #send-button.chat-disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            /* Style the chat input when disabled */
            #chat-input.chat-disabled {
                opacity: 0.7;
                background-color: rgba(200, 200, 200, 0.1);
                cursor: pointer;
            }
            
            /* Create a relative positioning context for the tooltip */
            .chat-input-tooltip {
                position: fixed;
                background-color: rgba(0, 0, 0, 0.7);
                color: rgba(255, 255, 255, 0.9);
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                pointer-events: none;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.15s ease;
                transform: translate(10px, -25px);
            }
        `;
        document.head.appendChild(styleElement);
    };
    
    // Create tooltip element for cursor following
    let tooltipEl = null;
    
    const setupTooltip = () => {
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'chat-input-tooltip';
        tooltipEl.textContent = 'Please select one of the options above';
        document.body.appendChild(tooltipEl);
        
        // Position the tooltip near the cursor when hovering over the disabled chat input
        chatInput.addEventListener('mousemove', (e) => {
            if (!chatEnabled) {
                tooltipEl.style.left = `${e.clientX}px`;
                tooltipEl.style.top = `${e.clientY}px`;
                tooltipEl.style.opacity = '1';
            }
        });
        
        chatInput.addEventListener('mouseleave', () => {
            tooltipEl.style.opacity = '0';
        });
    };
    
    // Update the UI based on permission state - now handles both elements
    const updateUI = () => {
        if (!sendButton || !chatInput) return;
        
        if (!chatEnabled) {
            sendButton.classList.add('chat-disabled');
            chatInput.classList.add('chat-disabled');
        } else {
            sendButton.classList.remove('chat-disabled');
            chatInput.classList.remove('chat-disabled');
            if (tooltipEl) {
                tooltipEl.style.opacity = '0';
            }
        }
    };
    
    // Disable chat sending with a reason
    const disableChat = (reason) => {
        chatEnabled = false;
        disabledReason = reason || 'Please select one of the options above to continue';
        updateUI();
    };
    
    // Enable chat sending
    const enableChat = () => {
        chatEnabled = true;
        disabledReason = '';
        updateUI();
    };
    
    // Override the sendMessage function to check permissions
    const overrideSendMessage = () => {
        // Store the original sendMessage function
        const originalSendMessage = window.sendMessage;
        
        // Replace with our permission-aware version
        window.sendMessage = function() {
            if (!chatEnabled) {
                // Just a subtle flash of the button to indicate it's disabled
                const originalColor = sendButton.style.backgroundColor;
                sendButton.style.backgroundColor = 'rgba(255, 59, 48, 0.3)';
                setTimeout(() => {
                    sendButton.style.backgroundColor = originalColor;
                }, 300);
                return false;
            }
            
            // If chat is enabled, call the original function
            return originalSendMessage.apply(this, arguments);
        };
    };
    
    // Register a component that will disable chat when it shows buttons
    const registerButtonComponent = (componentName, options = {}) => {
        pendingButtonSelections.push({
            name: componentName,
            disableMessage: options.disableMessage || `Please select an option for ${componentName}`
        });
        
        // If this is the first component added, disable chat
        if (pendingButtonSelections.length === 1) {
            disableChat(pendingButtonSelections[0].disableMessage);
        }
    };
    
    // Mark a component's buttons as selected (re-enable chat if all are done)
    const markButtonSelected = (componentName) => {
        // Remove the component from the pending list
        pendingButtonSelections = pendingButtonSelections.filter(c => c.name !== componentName);
        
        // If no more pending selections, enable chat
        if (pendingButtonSelections.length === 0) {
            enableChat();
        } else {
            // Otherwise update with the next component's message
            disableChat(pendingButtonSelections[0].disableMessage);
        }
    };
    
    // Initialize the manager
    const init = () => {
        setupUI();
        setupTooltip();
        overrideSendMessage();
        
        // Initial state is enabled
        enableChat();
    };
    
    // Initialize
    init();
    
    // Return public API
    return {
        disableChat,
        enableChat,
        registerButtonComponent,
        markButtonSelected,
        isChatEnabled: () => chatEnabled
    };
};

// Initialize and export
window.chatPermissions = createChatPermissionManager();
console.log('Chat Permission Manager created and assigned to window.chatPermissions');