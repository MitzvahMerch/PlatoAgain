// googleAdsEvents.js
// This file implements Google Ads event tracking for key conversion points:
// 1. First message sent
// 2. Logo upload
// 3. Add to checkout (quantity selection)
// 4. Payment completion

// Create a global tracking object to prevent duplicate events
window.googleAdsTracking = {
    firstMessageSent: false,
    logoUploaded: false,
    quantitySelected: false,  // NEW tracking flag
    paymentCompleted: false
};

// Track the first user message sent
function trackFirstMessage() {
    // Only track this once per session
    if (window.googleAdsTracking.firstMessageSent) {
        return;
    }
    
    console.log('Tracking first message conversion event');
    
    // Google Ads event snippet for first message (initiate conversation)
    gtag('event', 'conversion', {
        'send_to': 'AW-16970928099/w1iyCKmP_LQaEOOfr5w_',
        'value': 1.0, // Assigning a $1.00 value to starting a conversation
        'currency': 'USD',
        'transaction_id': `msg_${Date.now()}_${userId}`
    });
    
    // Mark as tracked
    window.googleAdsTracking.firstMessageSent = true;
}

// Track logo upload
function trackLogoUpload(logoFilename) {
    // Only track this once per session
    if (window.googleAdsTracking.logoUploaded) {
        return;
    }
    
    console.log('Tracking logo upload conversion event');
    
    // Google Ads event snippet for logo upload
    gtag('event', 'conversion', {
        'send_to':  'AW-16970928099/aT3KCKGI77QaEOOfr5w_',
        'value': 1.0, // Assigning a $1 value to uploading a logo
        'currency': 'USD',
        'transaction_id': `logo_${Date.now()}_${userId}`
    });
    
    // Mark as tracked
    window.googleAdsTracking.logoUploaded = true;
}

// NEW FUNCTION: Track quantity selection (Add to Checkout equivalent)
function trackQuantitySelection(totalQuantity) {
    // Only track this once per session
    if (window.googleAdsTracking.quantitySelected) {
        return;
    }
    
    console.log(`Tracking quantity selection conversion event with ${totalQuantity} items`);
    
    // Google Ads event snippet for quantity selection (add to checkout)
    gtag('event', 'conversion', {
        'send_to': 'AW-16970928099/p6XqCJKMiLYaEOOfr5w_', // This would be your actual add_to_checkout event ID
        'value': totalQuantity * 0.5, // Assigning value based on quantity ($0.50 per item as an example)
        'currency': 'USD',
        'transaction_id': `qty_${Date.now()}_${userId}`
    });
    
    // Mark as tracked
    window.googleAdsTracking.quantitySelected = true;
}

// Track payment completion
function trackPaymentCompletion(paymentDetails) {
    // Only track this once per session
    if (window.googleAdsTracking.paymentCompleted) {
        return;
    }
    
    // Extract payment amount if available
    let value = 1.0; // Default value
    if (paymentDetails && paymentDetails.orderData && 
        paymentDetails.orderData.purchase_units && 
        paymentDetails.orderData.purchase_units.length > 0) {
        const amount = paymentDetails.orderData.purchase_units[0].amount;
        if (amount && amount.value) {
            value = parseFloat(amount.value);
        }
    }
    
    console.log(`Tracking payment completion conversion event with value: $${value}`);
    
    // Google Ads event snippet for payment
    gtag('event', 'conversion', {
        'send_to': 'AW-16970928099/mkXNCP_68LIaEOOfr5w_',
        'value': value,
        'currency': 'USD',
        'transaction_id': `payment_${Date.now()}_${userId}`
    });
    
    // Mark as tracked
    window.googleAdsTracking.paymentCompleted = true;
}

// Export the tracking functions
window.googleAdsEvents = {
    trackFirstMessage,
    trackLogoUpload,
    trackQuantitySelection, // NEW: Add this function to the exports
    trackPaymentCompletion
};

console.log('Google Ads event tracking initialized with quantity selection support');