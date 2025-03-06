// paypalIntegration.js
// This adds the PayPal payment button directly into Plato's chat messages
// Based on similar patterns used in shippingFormInChat.js and quantitySelector.js

const createPayPalIntegration = () => {
    console.log('Initializing PayPal SDK integration...');

    // Add the CSS styles for the PayPal integration
    const addStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .paypal-container {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                width: 100%;
            }
            
            .paypal-header {
                margin: 0 0 15px 0;
                font-size: 16px;
                color: var(--secondary-color);
                font-weight: 500;
                text-align: center;
            }
            
            .order-summary {
                margin-bottom: 20px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                color: white;
            }
            
            .order-summary h3 {
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 14px;
                color: var(--secondary-color);
            }
            
            .paypal-button-container {
                width: 100%;
                transition: opacity 0.3s;
            }
            
            .payment-success {
                display: none;
                text-align: center;
                padding: 15px;
                margin-top: 15px;
                background: rgba(76, 175, 80, 0.2);
                border-radius: 4px;
                color: white;
            }
            
            .payment-success.visible {
                display: block;
            }
            
            .payment-error {
                display: none;
                text-align: center;
                padding: 15px;
                margin-top: 15px;
                background: rgba(244, 67, 54, 0.2);
                border-radius: 4px;
                color: white;
            }
            
            .payment-error.visible {
                display: block;
            }
            
            .paypal-loading {
                text-align: center;
                margin: 20px 0;
                color: white;
            }
            
            .paypal-loading-spinner {
                display: inline-block;
                width: 30px;
                height: 30px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
                margin-bottom: 10px;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        
        document.head.appendChild(styleElement);
    };

    // Load the PayPal SDK
    const loadPayPalSDK = (clientId) => {
        return new Promise((resolve, reject) => {
            // Check if SDK is already loaded
            if (window.paypal) {
                resolve(window.paypal);
                return;
            }
            
            // Create script element for PayPal SDK
            const script = document.createElement('script');
            script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&currency=USD&components=buttons&intent=capture`;
            script.async = true;
            
            // Handle script load events
            script.onload = () => {
                console.log('PayPal SDK loaded successfully');
                resolve(window.paypal);
            };
            
            script.onerror = () => {
                console.error('Failed to load PayPal SDK');
                reject(new Error('Failed to load PayPal SDK'));
            };
            
            // Add script to document
            document.body.appendChild(script);
        });
    };

    // Parse PayPal invoice URL to extract relevant information
    const parsePayPalInvoiceUrl = (messageText) => {
        // Look for payment URL pattern
        const urlRegex = /https:\/\/www\.paypal\.com\/invoice\/p\/#([a-zA-Z0-9]+)/;
        const match = messageText.match(urlRegex);
        
        if (match && match[1]) {
            return {
                fullUrl: match[0],
                invoiceId: match[1]
            };
        }
        
        return null;
    };

    // Extract order details from the message
    const extractOrderDetails = (messageText) => {
        // Extract total price
        const priceRegex = /\$(\d+\.\d{2})/;
        const priceMatch = messageText.match(priceRegex);
        const totalPrice = priceMatch ? priceMatch[1] : '0.00';
        
        // Extract customer name
        const nameRegex = /Thanks\s+([^,!.]+)/i;
        const nameMatch = messageText.match(nameRegex);
        const customerName = nameMatch ? nameMatch[1].trim() : 'Customer';
        
        // Extract quantity and product info (simplified)
        const quantityRegex = /order\s+(?:of|for)\s+(.+?)(?=\s+of\s+|\s+for\s+|\s+\$)/i;
        const quantityMatch = messageText.match(quantityRegex);
        const quantityInfo = quantityMatch ? quantityMatch[1].trim() : 'items';
        
        // Extract product info
        const productRegex = /of\s+(.+?)(?=\.\s+Total|\s+for\s+\$)/i;
        const productMatch = messageText.match(productRegex);
        const productInfo = productMatch ? productMatch[1].trim() : 'Custom Product';
        
        return {
            totalPrice,
            customerName,
            quantityInfo,
            productInfo
        };
    };

    // Create the PayPal button component
    const createPayPalButton = async (container, invoiceDetails, orderDetails) => {
        try {
            // Add loading indicator while we initialize PayPal
            const loadingElement = document.createElement('div');
            loadingElement.className = 'paypal-loading';
            
            const spinner = document.createElement('div');
            spinner.className = 'paypal-loading-spinner';
            
            const loadingText = document.createElement('div');
            loadingText.textContent = 'Loading payment options...';
            
            loadingElement.appendChild(spinner);
            loadingElement.appendChild(loadingText);
            container.appendChild(loadingElement);
            
            // Initialize PayPal SDK with your client ID
            // In a production environment, this would be securely configured
            const clientId = 'Aa2-mzkmjWQCgXq3zONHNu1eFWPABooevh0Hjp_z7PMBjZOJ0xdCIAIgE4eK8MJ4TcowsMROEefprlvm'; // Live client ID
            const paypal = await loadPayPalSDK(clientId);
            
            // Remove loading indicator
            loadingElement.remove();
            
            // Create the button container
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'paypal-button-container';
            container.appendChild(buttonContainer);
            
            // Add success and error message containers
            const successMessage = document.createElement('div');
            successMessage.className = 'payment-success';
            successMessage.innerHTML = '<strong>Payment Successful!</strong><p>Thank you for your order. You will receive a confirmation email shortly.</p>';
            container.appendChild(successMessage);
            
            const errorMessage = document.createElement('div');
            errorMessage.className = 'payment-error';
            errorMessage.innerHTML = '<strong>Payment Error</strong><p>There was a problem processing your payment. Please try again or contact support.</p>';
            container.appendChild(errorMessage);
            
            // Render the PayPal button
            paypal.Buttons({
                // Set up the transaction
                createOrder: (data, actions) => {
                    // Extract the amount from the order details
                    const amount = parseFloat(orderDetails.totalPrice);
                    
                    // Create a PayPal order
                    return actions.order.create({
                        purchase_units: [{
                            description: `Order for ${orderDetails.customerName}`,
                            amount: {
                                value: amount,
                                currency_code: 'USD'
                            },
                            invoice_id: invoiceDetails.invoiceId // Use the invoice ID from the URL
                        }]
                    });
                },
                
                // Handle the successful payment
                onApprove: async (data, actions) => {
                    try {
                        // Capture the funds from the transaction
                        const orderData = await actions.order.capture();
                        
                        console.log('Payment successful:', orderData);
                        
                        // Update UI to show success
                        buttonContainer.style.opacity = '0.5';
                        successMessage.classList.add('visible');
                        
                        // Notify the backend about the successful payment
                        const response = await fetch(`${API_BASE_URL}/api/payment-complete`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                user_id: userId,
                                invoice_id: invoiceDetails.invoiceId,
                                payment_id: data.orderID,
                                payment_details: orderData
                            }),
                        });
                        
                        if (!response.ok) {
                            console.error('Error notifying backend of payment:', await response.text());
                        } else {
                            // Add a confirmation message from the bot
                            const typingIndicator = addTypingIndicator();
                            
                            setTimeout(() => {
                                typingIndicator.remove();
                                addMessage('Your payment has been received! Your order is now being processed. Thank you for your business!', 'bot');
                            }, 1500);
                        }
                    } catch (error) {
                        console.error('Error processing payment:', error);
                        errorMessage.classList.add('visible');
                    }
                },
                
                // Handle payment cancellation
                onCancel: (data) => {
                    console.log('Payment cancelled by user');
                },
                
                // Handle payment errors
                onError: (err) => {
                    console.error('PayPal Error:', err);
                    errorMessage.classList.add('visible');
                }
            }).render(buttonContainer);
            
        } catch (error) {
            console.error('Error creating PayPal button:', error);
            container.innerHTML = `
                <div class="payment-error visible">
                    <strong>Error Loading Payment Options</strong>
                    <p>There was a problem loading the payment system. Please use the direct PayPal link or contact support.</p>
                </div>
                <div style="margin-top:15px; text-align:center;">
                    <a href="${invoiceDetails.fullUrl}" target="_blank" rel="noopener" style="color:#0070ba; text-decoration:underline;">
                        Pay with PayPal directly
                    </a>
                </div>
            `;
        }
    };

    // Create the PayPal integration component
    const createPayPalComponent = (orderDetails, invoiceDetails) => {
        console.log('Creating PayPal integration with details:', { orderDetails, invoiceDetails });
        
        const container = document.createElement('div');
        container.className = 'paypal-container';
        
        // Header
        const header = document.createElement('div');
        header.className = 'paypal-header';
        header.textContent = 'Complete Your Payment';
        container.appendChild(header);
        
        // Order summary
        const orderSummary = document.createElement('div');
        orderSummary.className = 'order-summary';
        orderSummary.innerHTML = `
            <h3>Order Summary</h3>
            <p><strong>Customer:</strong> ${orderDetails.customerName}</p>
            <p><strong>Items:</strong> ${orderDetails.quantityInfo}</p>
            <p><strong>Product:</strong> ${orderDetails.productInfo}</p>
            <p><strong>Total:</strong> $${orderDetails.totalPrice}</p>
        `;
        container.appendChild(orderSummary);
        
        // Initialize the PayPal button
        createPayPalButton(container, invoiceDetails, orderDetails);
        
        return container;
    };

    // Main function to inject the PayPal integration into a message
    // Main function to inject the PayPal integration into a message
const injectPayPalIntegration = (messageElement) => {
    console.log('Injecting PayPal integration into message:', messageElement);
    
    // Don't inject if already done
    if (messageElement.querySelector('.paypal-container')) {
        console.log('PayPal integration already injected, skipping');
        return;
    }
    
    // Get the message text
    const messageText = messageElement.textContent;
    
    // Extract order details from the message
    const orderDetails = extractOrderDetails(messageText);
    console.log('Extracted order details:', orderDetails);
    
    // Create a dummy invoice details object since we're not using actual PayPal URLs anymore
    const dummyInvoiceDetails = {
        fullUrl: "#",
        invoiceId: "ORDER" + Date.now() // Generate a random ID
    };
    
    // Create and append the PayPal integration
    const paypalComponent = createPayPalComponent(orderDetails, dummyInvoiceDetails);
    messageElement.appendChild(paypalComponent);
};

    // Monitor for messages with PayPal invoice links
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
                        if (node.nodeType === Node.ELEMENT_NODE && 
                            node.classList.contains('message') && 
                            node.classList.contains('bot')) {
                            
                            // Check for order confirmation markers
                            const messageText = node.textContent;
                            
                            if (messageText.includes("# Order Confirmation") || 
                                messageText.includes("Warm regards, Plato") || 
                                messageText.includes("platosprints@gmail.com")) {
                                
                                console.log('Order confirmation detected in message');
                                injectPayPalIntegration(node);
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
        injectIntoMessage: injectPayPalIntegration,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

// Initialize and export the PayPal integration
console.log('Creating PayPal integration...');
window.paypalIntegration = createPayPalIntegration();
console.log('PayPal integration created and assigned to window.paypalIntegration');