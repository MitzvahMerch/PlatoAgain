// paypalIntegration.js
// This adds the PayPal payment button directly into Plato's chat messages
// Based on similar patterns used in shippingFormInChat.js and quantitySelector.js

const createPayPalIntegration = () => {
    console.log('Initializing PayPal SDK integration with Venmo support for all devices...');

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
            
            .venmo-button-container {
                width: 100%;
                margin-top: 10px;
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
            
            .payment-options-divider {
                text-align: center;
                margin: 15px 0;
                color: var(--secondary-color);
                font-size: 14px;
                position: relative;
            }
            
            .payment-options-divider:before,
            .payment-options-divider:after {
                content: "";
                display: inline-block;
                width: 40%;
                height: 1px;
                background: rgba(255, 255, 255, 0.2);
                position: absolute;
                top: 50%;
            }
            
            .payment-options-divider:before {
                left: 0;
            }
            
            .payment-options-divider:after {
                right: 0;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        
        document.head.appendChild(styleElement);
    };

    // Load the PayPal SDK with Venmo support
    const loadPayPalSDK = (clientId) => {
        return new Promise((resolve, reject) => {
            // Check if SDK is already loaded
            if (window.paypal) {
                resolve(window.paypal);
                return;
            }
            
            // Create script element for PayPal SDK with Venmo enabled
            const script = document.createElement('script');
            script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&currency=USD&components=buttons,funding-eligibility&intent=capture&enable-funding=venmo`;
            script.async = true;
            
            // Handle script load events
            script.onload = () => {
                console.log('PayPal SDK loaded successfully with Venmo support');
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
        const priceRegex = /totaling\s+\$(\d+\.\d{2})/i;
        const priceMatch = messageText.match(priceRegex);
        const totalPrice = priceMatch ? priceMatch[1] : '0.00';
        
        // Extract customer name
        const nameRegex = /Dear\s+([^,]+),/i;
        const nameMatch = messageText.match(nameRegex);
        const customerName = nameMatch ? nameMatch[1].trim() : 'Customer';
        
        // Extract quantity and product info
        const orderRegex = /order\s+of\s+(.+?)\s+Custom\s+(.+?),\s+totaling/i;
        const orderMatch = messageText.match(orderRegex);
        
        const quantityInfo = orderMatch ? orderMatch[1].trim() : 'undefined';
        const productInfo = orderMatch ? orderMatch[2].trim() : 'Custom Product';
        
        // Extract delivery date
        const dateRegex = /by\s+([^,]+),\s+as\s+requested/i;
        const dateMatch = messageText.match(dateRegex);
        const receivedByDate = dateMatch ? dateMatch[1].trim() : 'Standard delivery';
        
        return {
            totalPrice,
            customerName,
            quantityInfo,
            productInfo,
            receivedByDate
        };
    };

    // Create the PayPal button component with Venmo support
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
            
            // Common configuration for all payment methods
            const commonConfig = {
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
                        
                        // If we have a Venmo container, also reduce its opacity
                        const venmoContainer = container.querySelector('.venmo-button-container');
                        if (venmoContainer) {
                            venmoContainer.style.opacity = '0.5';
                        }
                        
                        successMessage.classList.add('visible');
                        
                        // Track payment completion for Google Ads
                        if (!window.googleAdsTracking?.paymentCompleted) {
                            // Extract payment amount if available
                            let value = orderDetails.totalPrice || 1.0; // Default to order total or $1
                            
                            if (orderData && 
                                orderData.purchase_units && 
                                orderData.purchase_units.length > 0 &&
                                orderData.purchase_units[0].amount &&
                                orderData.purchase_units[0].amount.value) {
                                value = parseFloat(orderData.purchase_units[0].amount.value);
                            }
                            
                            console.log(`Tracking payment completion conversion event with value: $${value}`);
                            
                            // Google Ads event snippet for payment
                            gtag('event', 'conversion', {
                                'send_to': 'AW-16970928099/mkXNCP_68LIaEOOfr5w_',
                                'value': value,
                                'currency': 'USD',
                                'transaction_id': `payment_${Date.now()}_${userId}`
                            });

                            if (window.googleAnalytics) {
                                // Prepare parameters for the standard GA4 'purchase' event
                                const purchaseParams = {
                                    transaction_id: data.orderID || `payment_${Date.now()}_${userId}`, // CRITICAL: Use PayPal Order ID or generate unique ID
                                    value: value, // The final numeric amount captured
                                    currency: 'USD',
                                    // Optional but recommended: more specific payment method
                                    payment_method: orderData.payment_source?.venmo ? 'Venmo' : (orderData.payment_source?.paypal ? 'PayPal' : 'Card/Other'),
                                    // Optional but HIGHLY recommended for e-commerce reporting: Items array
                                    // items: [{ // You need to populate this based on orderDetails
                                    //     item_id: 'YOUR_SKU_OR_PRODUCT_ID',
                                    //     item_name: orderDetails.productInfo || 'Custom Product',
                                    //     quantity: /* total quantity from orderDetails */,
                                    //     price: value / /* total quantity */ // Calculate unit price if possible
                                    // }]
                                };
                            
                                // Call trackFunnelStep with the 'payment' key, which maps to 'purchase' event
                                window.googleAnalytics.trackFunnelStep('payment', purchaseParams);
                            }
                            
                            // Mark as tracked to prevent duplicate events
                            if (!window.googleAdsTracking) window.googleAdsTracking = {};
                            window.googleAdsTracking.paymentCompleted = true;
                        }
                        
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
                                payment_details: orderData,
                                payment_method: orderData.payment_source || 'unknown'
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
            };
            
            // Render standard PayPal button (includes credit/debit options)
            paypal.Buttons({
                ...commonConfig,
                style: {
                    layout: 'vertical',
                    color: 'blue',
                    shape: 'rect',
                    label: 'pay'
                }
            }).render(buttonContainer);
            
            // Check if Venmo is available in the PayPal SDK
            if (paypal.FUNDING.VENMO) {
                try {
                    console.log('Adding Venmo payment option');
                    
                    // Add a divider between payment options
                    const divider = document.createElement('div');
                    divider.className = 'payment-options-divider';
                    divider.textContent = 'or';
                    container.appendChild(divider);
                    
                    // Create a separate container for Venmo
                    const venmoContainer = document.createElement('div');
                    venmoContainer.className = 'venmo-button-container';
                    container.appendChild(venmoContainer);
                    
                    // Render Venmo-specific button
                    paypal.Buttons({
                        ...commonConfig,
                        fundingSource: paypal.FUNDING.VENMO,
                        style: {
                            color: 'blue',
                            shape: 'rect'
                        }
                    }).render(venmoContainer);
                    
                    console.log('Venmo payment option added successfully');
                } catch (error) {
                    console.warn('Error rendering Venmo button:', error);
                }
            } else {
                console.log('Venmo funding option not available in this PayPal SDK instance');
            }
            
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
            <p><strong>Items:</strong> ${orderDetails.quantityInfo} Custom ${orderDetails.productInfo}</p>
            <p><strong>Receive By:</strong> ${orderDetails.receivedByDate || 'Standard delivery timeframe'}</p>
            <p><strong>Total:</strong> $${orderDetails.totalPrice}</p>
        `;
        container.appendChild(orderSummary);
        
        // Initialize the PayPal button with Venmo support
        createPayPalButton(container, invoiceDetails, orderDetails);
        
        return container;
    };

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
        
        // Permanently disable chat for the rest of the conversation once PayPal is shown
        if (window.chatPermissions) {
            window.chatPermissions.disableChat('Your order is being processed. Payment required to continue.');
        }
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
console.log('Creating PayPal integration with Venmo support for all devices...');
window.paypalIntegration = createPayPalIntegration();
console.log('PayPal integration created and assigned to window.paypalIntegration');