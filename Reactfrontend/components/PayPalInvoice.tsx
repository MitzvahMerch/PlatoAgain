// ReactFrontend/components/PayPalInvoice.tsx
import React from 'react'

export interface PayPalInvoiceProps {
  invoiceUrl: string
}

const PayPalInvoice: React.FC<PayPalInvoiceProps> = ({ invoiceUrl }) => (
  <div className="w-full h-96">
    <iframe
      src={invoiceUrl}
      title="PayPal Invoice"
      className="w-full h-full"
      frameBorder="0"
    />
  </div>
)

export default PayPalInvoice