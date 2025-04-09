// googleAnalytics.js
// Google Analytics 4 initialization and event tracking integration

// Check if gtag function already exists (from Google Ads implementation)
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
    console.log(`Tracking GA4 event: ${eventName}`, eventParams);
    gtag('event', eventName, eventParams);
}

// Function to track chat funnel events in GA4
function trackFunnelStep(step, additionalParams = {}) {
    // CHANGE THIS PART - Update with the exact event names from GA4
    const eventNames = {
        'first_message': 'firstChat',
        'logo_upload': 'logoUpload',
        'quantity_selection': 'QuantitySubmission',
        'payment': 'Purchase'
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
    trackFunnelStep: trackFunnelEvent
};

console.log('Google Analytics 4 initialized');