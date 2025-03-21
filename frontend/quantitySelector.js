// quantitySelector.js
// This adds an interactive quantity selector directly into Plato's chat message box

const createQuantitySelector = () => {
    console.log('Initializing quantity selector...');

    // Default sizes if we can't parse them from the message
    const DEFAULT_SIZES = {
        youth: ['XS', 'S', 'M', 'L', 'XL'],
        adult: ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL']
    };

    // Helper to parse size ranges from message text
    // Format expected: "...youth sizes XS-XL and adult sizes XS-4XL..."
    const parseSizesFromMessage = (messageText) => {
        const sizes = {
            youth: [],
            adult: []
        };

        try {
            // Parse youth sizes (format: "youth sizes X-Y")
            const youthMatch = messageText.match(/youth\s+sizes\s+([A-Za-z0-9]+)-([A-Za-z0-9]+)/i);
            if (youthMatch && youthMatch.length >= 3) {
                const startSize = youthMatch[1].toUpperCase();
                const endSize = youthMatch[2].toUpperCase();
                sizes.youth = expandSizeRange(startSize, endSize);
            } else {
                console.log('Could not parse youth sizes, using defaults');
                sizes.youth = DEFAULT_SIZES.youth;
            }

            // Parse adult sizes (format: "adult sizes X-Y")
            const adultMatch = messageText.match(/adult\s+sizes\s+([A-Za-z0-9]+)-([A-Za-z0-9]+)/i);
            if (adultMatch && adultMatch.length >= 3) {
                const startSize = adultMatch[1].toUpperCase();
                const endSize = adultMatch[2].toUpperCase();
                sizes.adult = expandSizeRange(startSize, endSize);
            } else {
                console.log('Could not parse adult sizes, using defaults');
                sizes.adult = DEFAULT_SIZES.adult;
            }

            return sizes;
        } catch (error) {
            console.error('Error parsing sizes from message:', error);
            return DEFAULT_SIZES;
        }
    };

    // Helper to expand size ranges like "XS-XL" to ["XS", "S", "M", "L", "XL"]
    const expandSizeRange = (startSize, endSize) => {
        const sizeOrder = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'];
        
        // Handle numeric prefixes like "4XL"
        // If we see a numeric prefix, we need to normalize
        const normalizeSize = (size) => {
            if (size.match(/^\d+XL$/i)) {
                return size.toUpperCase();
            }
            return size.toUpperCase();
        };
        
        const normalizedStart = normalizeSize(startSize);
        const normalizedEnd = normalizeSize(endSize);
        
        const startIndex = sizeOrder.indexOf(normalizedStart);
        const endIndex = sizeOrder.indexOf(normalizedEnd);
        
        if (startIndex === -1 || endIndex === -1 || startIndex > endIndex) {
            console.error(`Invalid size range: ${startSize}-${endSize}`);
            return DEFAULT_SIZES.adult; // Fallback to defaults
        }
        
        return sizeOrder.slice(startIndex, endIndex + 1);
    };

    // Helper to create a size selector row
    // Helper to create a size selector row
const createSizeRow = (size, type) => {
    const sizeKey = `${type.toLowerCase()}_${size.toLowerCase().replace(/xl/i, 'XL')}`;
    
    const row = document.createElement('div');
    row.className = 'quantity-size-row';
    
    const label = document.createElement('div');
    label.className = 'quantity-size-label';
    label.textContent = `${type} ${size}`;
    
    const controls = document.createElement('div');
    controls.className = 'quantity-controls';
    
    const minusBtn = document.createElement('button');
    minusBtn.className = 'quantity-btn quantity-btn-minus';
    minusBtn.textContent = '-';
    minusBtn.setAttribute('data-size', sizeKey);
    minusBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent form submission
        e.stopPropagation(); // Prevent event from bubbling
        const input = controls.querySelector('.quantity-input');
        let value = parseInt(input.value) || 0;
        if (value > 0) {
            input.value = value - 1;
            input.dispatchEvent(new Event('change'));
        }
    });
    
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'quantity-input';
    input.min = '0';
    input.value = '0';
    input.setAttribute('data-size', sizeKey);

    // Clear the default '0' when the field is focused
    input.addEventListener('focus', (e) => {
        if (e.target.value === '0') {
            e.target.value = '';
        }
    });
    
    // If the field is left empty on blur, reset it to '0'
    input.addEventListener('blur', (e) => {
        if (e.target.value === '') {
            e.target.value = '0';
            updateTotals();
        }
    });
    
    input.addEventListener('change', updateTotals);
    input.addEventListener('input', (e) => {
        // Ensure input is a non-negative integer
        let value = e.target.value.replace(/[^0-9]/g, '');
        if (value === '') value = '0';
        e.target.value = value;
        updateTotals();
    });
    
    const plusBtn = document.createElement('button');
    plusBtn.className = 'quantity-btn quantity-btn-plus';
    plusBtn.textContent = '+';
    plusBtn.setAttribute('data-size', sizeKey);
    plusBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent form submission
        e.stopPropagation(); // Prevent event from bubbling
        const input = controls.querySelector('.quantity-input');
        let value = parseInt(input.value) || 0;
        input.value = value + 1;
        input.dispatchEvent(new Event('change'));
    });
    
    controls.appendChild(minusBtn);
    controls.appendChild(input);
    controls.appendChild(plusBtn);
    
    row.appendChild(label);
    row.appendChild(controls);
    
    return row;
};

    // Update total quantities and trigger notification
    function updateTotals() {
        const container = document.querySelector('.quantity-selector-container');
        if (!container) return;
        
        const inputs = container.querySelectorAll('.quantity-input');
        let totalQuantity = 0;
        let sizesSelected = {};
        
        inputs.forEach(input => {
            const value = parseInt(input.value) || 0;
            if (value > 0) {
                totalQuantity += value;
                const sizeKey = input.getAttribute('data-size');
                sizesSelected[sizeKey] = value;
            }
        });
        
        // Update the total display
        const totalElement = container.querySelector('.quantity-total');
        if (totalElement) {
            totalElement.textContent = `Total: ${totalQuantity} items`;
        }
        
        // Store the selected quantities
        window.selectedQuantities = sizesSelected;
        
        // Enable/disable the submit button based on whether any quantities are selected
        const submitBtn = container.querySelector('.quantity-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = totalQuantity === 0;
            submitBtn.classList.toggle('quantity-submit-btn-active', totalQuantity > 0);
        }
    }

    // Create the complete quantity selector UI based on available sizes
    const createQuantitySelector = (messageText) => {
        const parsedSizes = parseSizesFromMessage(messageText);
        console.log('Parsed sizes for selector:', parsedSizes);
        
        const container = document.createElement('div');
        container.className = 'quantity-selector-container';
        
        // Only show youth sizes section if youth sizes are available
        if (parsedSizes.youth && parsedSizes.youth.length > 0) {
            const youthSection = document.createElement('div');
            youthSection.className = 'quantity-section youth-section';
            
            // Create header with dropdown toggle
            const youthHeaderContainer = document.createElement('div');
            youthHeaderContainer.className = 'quantity-section-header-container';
            
            const youthHeader = document.createElement('h4');
            youthHeader.className = 'quantity-section-header';
            youthHeader.textContent = 'Youth Sizes';
            
            const dropdownIcon = document.createElement('span');
            dropdownIcon.className = 'dropdown-icon';
            dropdownIcon.innerHTML = '▼';
            dropdownIcon.style.transform = 'rotate(-90deg)'; // Point right when collapsed
            
            youthHeaderContainer.appendChild(youthHeader);
            youthHeaderContainer.appendChild(dropdownIcon);
            youthSection.appendChild(youthHeaderContainer);
            
            // Create content container (initially hidden)
            const youthContent = document.createElement('div');
            youthContent.className = 'quantity-section-content';
            youthContent.style.display = 'none'; // Hidden by default
            
            // Add all youth sizes to the content container
            parsedSizes.youth.forEach(size => {
                youthContent.appendChild(createSizeRow(size, 'Youth'));
            });
            
            youthSection.appendChild(youthContent);
            
            // Add click handler to toggle visibility
            youthHeaderContainer.addEventListener('click', () => {
                const isHidden = youthContent.style.display === 'none';
                youthContent.style.display = isHidden ? 'block' : 'none';
                dropdownIcon.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
            });
            
            container.appendChild(youthSection);
        }
        
        // For adult sizes, modify the section to hide larger sizes:
        if (parsedSizes.adult && parsedSizes.adult.length > 0) {
            const adultSection = document.createElement('div');
            adultSection.className = 'quantity-section adult-section';
            
            const adultHeader = document.createElement('h4');
            adultHeader.className = 'quantity-section-header';
            adultHeader.textContent = 'Adult Sizes';
            adultSection.appendChild(adultHeader);
            
            // Separate standard and extended sizes
            const standardSizes = parsedSizes.adult.filter(size => 
                ['XS', 'S', 'M', 'L', 'XL'].includes(size));
            const extendedSizes = parsedSizes.adult.filter(size => 
                !['XS', 'S', 'M', 'L', 'XL'].includes(size));
            
            // Add standard sizes directly
            standardSizes.forEach(size => {
                adultSection.appendChild(createSizeRow(size, 'Adult'));
            });
            
            // Create extended sizes container if any exist
            if (extendedSizes.length > 0) {
                const extendedSizesContainer = document.createElement('div');
                extendedSizesContainer.className = 'extended-sizes-container';
                extendedSizesContainer.style.display = 'none'; // Hidden by default
                
                extendedSizes.forEach(size => {
                    extendedSizesContainer.appendChild(createSizeRow(size, 'Adult'));
                });
                
                // Create "Show more" button
                const showMoreBtn = document.createElement('button');
                showMoreBtn.className = 'show-more-btn';
                showMoreBtn.textContent = 'Show more sizes';
                showMoreBtn.addEventListener('click', () => {
                    const isHidden = extendedSizesContainer.style.display === 'none';
                    extendedSizesContainer.style.display = isHidden ? 'block' : 'none';
                    showMoreBtn.textContent = isHidden ? 'Show fewer sizes' : 'Show more sizes';
                });
                
                adultSection.appendChild(showMoreBtn);
                adultSection.appendChild(extendedSizesContainer);
            }
            
            container.appendChild(adultSection);
        }
        
        // Total and submit button
        const footer = document.createElement('div');
        footer.className = 'quantity-footer';
        
        const totalDisplay = document.createElement('div');
        totalDisplay.className = 'quantity-total';
        totalDisplay.textContent = 'Total: 0 items';
        
        const submitBtn = document.createElement('button');
        submitBtn.className = 'quantity-submit-btn';
        submitBtn.textContent = 'Confirm Quantities';
        submitBtn.disabled = true;
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleQuantitySubmission();
        });
        
        footer.appendChild(totalDisplay);
        footer.appendChild(submitBtn);
        
        // Assemble the container
        container.appendChild(footer);
        
        return container;
    };

    // Process the quantity submission
    function handleQuantitySubmission() {
        // Extract the selected quantities
        const quantities = window.selectedQuantities;
        if (!quantities || Object.keys(quantities).length === 0) {
            console.error('No quantities selected');
            return;
        }
        
        console.log('Selected quantities:', quantities);
        
        // Calculate total quantity
        let totalQuantity = 0;
        for (const quantity of Object.values(quantities)) {
            totalQuantity += parseInt(quantity);
        }
        
        // Check if total quantity is less than 24
        if (totalQuantity < 24) {
            // Show error message
            showMinimumQuantityError();
            return;
        }
        
        // Format the quantities as a message that matches the expected patterns
        let message = '';
        for (const [sizeKey, quantity] of Object.entries(quantities)) {
            // Convert keys like "youth_s" to "YS" and "adult_2xl" to "2XL"
            const [type, size] = sizeKey.split('_');
            
            if (type.toLowerCase() === 'youth') {
                // Format as "30 YS" for youth sizes
                message += `${quantity} Y${size.toUpperCase()}, `;
            } else {
                // Format as "30 L" for adult sizes (no "Adult" prefix)
                message += `${quantity} ${size.toUpperCase()}, `;
            }
        }
        
        message = message.slice(0, -2); // Remove trailing comma and space
        
        // Send the message through the chat
        const chatInput = document.getElementById('chat-input');
        chatInput.value = message;
        
        // Trigger the send button click to send the message
        document.getElementById('send-button').click();
    }
    
    // Show error for minimum quantity
function showMinimumQuantityError() {
    const container = document.querySelector('.quantity-selector-container');
    
    // Remove any existing error message
    const existingError = container.querySelector('.quantity-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'quantity-error-message';
    errorMessage.textContent = 'Minimum quantity: 24';
    errorMessage.style.color = '#ff3333';
    errorMessage.style.fontSize = '14px';
    errorMessage.style.marginTop = '10px';
    errorMessage.style.textAlign = 'right';
    errorMessage.style.fontWeight = 'bold';
    
    // Add error to the footer
    const footer = container.querySelector('.quantity-footer');
    footer.appendChild(errorMessage);
    
    // Add animation effect to highlight the error
    errorMessage.style.animation = 'shake 0.5s';
    
    // Also shake the total display for emphasis
    const totalDisplay = container.querySelector('.quantity-total');
    totalDisplay.style.color = '#ff3333';
    totalDisplay.style.animation = 'shake 0.5s';
    
    // Reset color after animation
    setTimeout(() => {
        totalDisplay.style.color = 'white';
    }, 1500);
}

    // Add the CSS styles for the quantity selector
    const addStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .quantity-selector-container {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                width: 100%;
            }
            
            .quantity-section {
                margin-bottom: 15px;
            }
            
            .quantity-section-header {
                margin: 0 0 8px 0;
                font-size: 14px;
                color: var(--secondary-color);
                font-weight: 500;
            }
            
            .quantity-size-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            .quantity-size-label {
                flex-grow: 1;
                color: white;
            }
            
            .quantity-controls {
                display: flex;
                align-items: center;
                border-radius: 4px;
                overflow: hidden;
                background: rgba(255, 255, 255, 0.15);
            }
            
            .quantity-btn {
                width: 30px;
                height: 30px;
                border: none;
                background: transparent;
                color: white;
                font-size: 16px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s;
            }
            
            .quantity-btn:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            .quantity-input {
                width: 40px;
                height: 30px;
                border: none;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                text-align: center;
                -moz-appearance: textfield;
            }
            
            .quantity-input::-webkit-outer-spin-button,
            .quantity-input::-webkit-inner-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }

            .quantity-section-header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    padding: 5px 0;
}

.quantity-section-header {
    margin: 0;
}

.dropdown-icon {
    font-size: 10px;
    transition: transform 0.2s ease;
}

.show-more-btn {
    background: transparent;
    border: none;
    color: var(--secondary-color);
    cursor: pointer;
    font-size: 12px;
    padding: 5px 0;
    text-align: left;
    width: 100%;
    margin-top: 5px;
}

.show-more-btn:hover {
    text-decoration: underline;
}

            
            .quantity-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .quantity-total {
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
            
            .quantity-submit-btn {
                padding: 8px 16px;
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                opacity: 0.7;
                transition: opacity 0.2s;
            }

            @keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}
            
            
            .quantity-submit-btn:disabled {
                cursor: not-allowed;
                opacity: 0.5;
            }
            
            .quantity-submit-btn-active {
                opacity: 1;
            }
        `;
        
        document.head.appendChild(styleElement);
    };

    // Main function to inject the selector into a message
    const injectQuantitySelector = (messageElement) => {
        console.log('Injecting quantity selector into message:', messageElement);
        
        // Don't inject if already done
        if (messageElement.querySelector('.quantity-selector-container')) {
            console.log('Quantity selector already injected, skipping');
            return;
        }
        
        // Get the message text for size parsing
        const messageText = messageElement.textContent;
        
        // Create and append the selector
        const selector = createQuantitySelector(messageText);
        messageElement.appendChild(selector);
        
        // Initialize totals
        updateTotals();
    };

    // Main function to monitor messages and detect quantity prompts
    const observeMessages = () => {
        console.log('Starting to observe chat messages for quantity prompts');
        
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
                            
                            // Check if this message is asking about quantities
                            const messageText = node.textContent.toLowerCase();
                            if ((messageText.includes('how many of each size would you like to order') || 
                                 messageText.includes('how many of each size')) && 
                                (messageText.includes('youth size') || 
                                 messageText.includes('adult size'))) {
                                
                                console.log('Quantity prompt detected:', messageText);
                                injectQuantitySelector(node);
                            }
                        }
                    });
                }
            });
        });
        
        // Start observing
        observer.observe(chatMessages, { childList: true });
        
        return observer;
    };

    // Initialize by adding styles and setting up the observer
    addStyles();
    const observer = observeMessages();
    
    // Return public API
    return {
        injectIntoMessage: injectQuantitySelector,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

// Initialize and export the quantity selector
console.log('Creating quantity selector...');
window.quantitySelector = createQuantitySelector();
console.log('Quantity selector created and assigned to window.quantitySelector');
