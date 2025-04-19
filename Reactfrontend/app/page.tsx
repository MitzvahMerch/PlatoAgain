// ReactFrontend/app/page.tsx
import Head from 'next/head'
import Script from 'next/script'
import ChatContainer from '../components/ChatContainer'

export default function Page() {
  return (
    <>
      <Head>
        <meta charSet="UTF-8" />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
        />
        <title>
          Plato Prints | AI Agent for Fast Bulk Custom Clothing Orders (24+)
        </title>
        <meta
          name="description"
          content="Use Plato Prints AI chat agent for easy bulk custom clothing orders (24+ units). Get fast quotes on shirts & more from PlatosPrints.ai. Mobile-first."
        />
        <link rel="icon" href="/images/BlackPlato.png" type="image/png" />
        <link
          rel="shortcut icon"
          href="/images/BlackPlato.png"
          type="image/png"
        />
        <link rel="apple-touch-icon" href="/images/BlackPlato.png" />
        <meta
          name="google-site-verification"
          content="UCtKrXt9Dm9Y5Uh5p6qpnOcvrb2OfrGPX_ZGg1aFyhs"
        />
        {/* Organization JSON‑LD */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: `{
  "@context":"https://schema.org",
  "@type":"Organization",
  "name":"Plato Prints",
  "alternateName":"PlatosPrints.ai",
  "url":"https://platosprints.ai/",
  "logo":"https://platosprints.ai/images/BlackPlato.png",
  "description":"Plato Prints offers fast, easy bulk custom apparel ordering (24+ units minimum) via an AI chat agent. Get instant quotes for t-shirts, hoodies, and more directly from your phone using PlatosPrints.ai.",
  "contactPoint":{"@type":"ContactPoint","contactType":"Customer Service"}
}`
          }}
        />
        {/* Service JSON‑LD */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: `{
  "@context":"https://schema.org",
  "@type":"Service",
  "serviceType":"Custom Apparel Printing",
  "provider":{"@type":"Organization","name":"Plato Prints"},
  "name":"AI-Powered Bulk Custom Clothing Orders",
  "description":"Order bulk custom clothing (24+ units minimum) like t-shirts, hoodies, polos easily and quickly through the PlatosPrints.ai chat interface. Get instant quotes and mobile-first service.",
  "areaServed":{"@type":"Country","name":"USA"}
}`
          }}
        />
      </Head>

      {/* Google Ads & GA4 */}
      <Script
        strategy="afterInteractive"
        src="https://www.googletagmanager.com/gtag/js?id=AW-16970928099"
      />
      <Script id="gtag-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);} 
          gtag('js', new Date());
          gtag('config','AW-16970928099');
        `}
      </Script>
      <Script
        strategy="afterInteractive"
        src="https://www.googletagmanager.com/gtag/js?id=G-4QZQTD6P0F"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);} 
          gtag('js', new Date());
          gtag('config','G-4QZQTD6P0F');
        `}
      </Script>

      {/* Meta Pixel */}
      <Script id="fb-pixel" strategy="afterInteractive">
        {`
          !function(f,b,e,v,n,t,s){
            if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)
          }(window, document,'script','https://connect.facebook.net/en_US/fbevents.js');
          fbq('init','2380726612294744');
          fbq('track','PageView');
        `}
      </Script>
      <noscript>
        <img
          height="1"
          width="1"
          style={{ display: 'none' }}
          src="https://www.facebook.com/tr?id=2380726612294744&ev=PageView&noscript=1"
          alt=""
        />
      </noscript>

      {/* Chat Shell */}
      <div className="chat-container flex flex-col h-screen bg-white">
        <ChatContainer />
      </div>

      {/* Upload Progress Overlay */}
      <div
        id="upload-progress"
        className="upload-progress hidden fixed inset-0 bg-black/50 flex items-center justify-center p-4"
      >
        <div className="bg-white rounded-lg p-4 w-full max-w-sm">
          <div className="progress-text text-sm mb-2" />
          <div className="progress-bar bg-gray-200 h-2 rounded">
            <div className="progress-fill bg-blue-600 h-2 rounded" />
          </div>
        </div>
      </div>
    </>
  )
}
