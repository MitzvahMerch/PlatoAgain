if (typeof gtag !== 'function') {
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    window.gtag = gtag; // Make sure it's accessible globally
    gtag('js', new Date());
}

// Configure GA4 tracking
gtag('config', 'G-4QZQTD6P0F');

// GA4-specific event tracking functions
function trackGA4Event(eventName, eventParams = {}) {
    // Automatically include userId if available and not already present
    if (typeof userId !== 'undefined' && userId && !eventParams.user_id) {
        eventParams.user_id = userId;
    }
    console.log(`Tracking GA4 event: ${eventName}`, eventParams);
    gtag('event', eventName, eventParams);
}

// Function to track chat funnel events in GA4
function trackFunnelStep(step, additionalParams = {}) {
    // CORRECTED event names map
    const eventNames = {
        'first_message': 'begin_chat',          // Use GA4 standard name
        'logo_upload': 'upload_logo',         // Custom name (snake_case)
        'quantity_selection': 'confirm_quantities', // Custom name (snake_case)
        'payment': 'purchase'             // *** Use GA4 standard 'purchase' name (lowercase) ***
    };

    const eventName = eventNames[step];
    if (!eventName) {
        console.error(`Unknown funnel step: ${step}`);
        return;
    }

    trackGA4Event(eventName, additionalParams);
}

// Export GA4 tracking functions
window.googleAnalytics = {
    trackEvent: trackGA4Event,
    trackFunnelStep: trackFunnelStep // CORRECTED TYPO: Changed trackFunnelEvent to trackFunnelStep
};

console.log('Google Analytics 4 initialized');