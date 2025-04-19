// ReactFrontend/lib/googleAnalytics.ts

type Gtag = (...args: any[]) => void;

declare global {
  interface Window {
    dataLayer: any[];
    gtag: Gtag;
    googleAnalytics: {
      trackEvent: (eventName: string, eventParams?: Record<string, any>) => void;
      trackFunnelStep: (step: FunnelStep, additionalParams?: Record<string, any>) => void;
    };
    userId?: string;
  }
}

export type FunnelStep = 'first_message' | 'logo_upload' | 'quantity_selection' | 'payment';

if (typeof window.gtag !== 'function') {
  window.dataLayer = window.dataLayer || [];
  const gtag: Gtag = (...args) => {
    window.dataLayer.push(args);
  };
  window.gtag = gtag;
  window.gtag('js', new Date());
}

// Configure GA4 tracking
window.gtag('config', 'G-4QZQTD6P0F');

/**
 * Tracks a GA4 event, automatically attaching user_id if available.
 */
export function trackEvent(
  eventName: string,
  eventParams: Record<string, any> = {}
): void {
  if (window.userId && !eventParams.user_id) {
    eventParams.user_id = window.userId;
  }
  console.log(`Tracking GA4 event: ${eventName}`, eventParams);
  window.gtag('event', eventName, eventParams);
}

// Map of funnel steps to GA4 event names
const funnelEventNames: Record<FunnelStep, string> = {
  first_message: 'begin_chat',
  logo_upload: 'upload_logo',
  quantity_selection: 'confirm_quantities',
  payment: 'purchase',
};

/**
 * Tracks a step in the chat funnel.
 */
export function trackFunnelStep(
  step: FunnelStep,
  additionalParams: Record<string, any> = {}
): void {
  const eventName = funnelEventNames[step];
  if (!eventName) {
    console.error(`Unknown funnel step: ${step}`);
    return;
  }
  trackEvent(eventName, additionalParams);
}

// Expose tracking functions globally
window.googleAnalytics = {
  trackEvent,
  trackFunnelStep,
};

console.log('Google Analytics 4 initialized');

export {};