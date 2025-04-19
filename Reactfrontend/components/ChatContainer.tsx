// ReactFrontend/components/ChatContainer.tsx
import React, { useState, useEffect, useRef } from 'react';
import ChatInput from './ChatInput';
import ProductButtons, { ProductInfo } from './ProductButtons';
import QuantitySelector, { QuantitySelectorProps } from './QuantitySelector';
import ShippingForm, { ShippingFormData } from './ShippingForm';
import PlacementModal from './PlacementModal';
import Spinner from './Spinner';
import DesignPlacer from './DesignPlacer';
import { svgBasedCompositeRenderer } from '../lib/compositeRenderer';
import { chatPermissions } from '../lib/chatPermissions';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

function generateUserId(): string {
  const id = `user_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
  localStorage.setItem('userId', id);
  return id;
}

const ChatContainer: React.FC = () => {
  const [userId] = useState<string>(() => localStorage.getItem('userId') || generateUserId());
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [showShipping, setShowShipping] = useState<boolean>(false);
  const [shippingDetails, setShippingDetails] = useState<any>(null);
  const [showPlacement, setShowPlacement] = useState<boolean>(false);
  const [placementProps, setPlacementProps] = useState<any>(null);
  const [quantityAction, setQuantityAction] = useState<QuantitySelectorProps | null>(null);
  const [productAction, setProductAction] = useState<ProductInfo | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages or loading
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const addMessage = (text: string, sender: 'user'|'bot'|'system', action?: any, images?: any[]) => {
    setMessages(prev => [...prev, { id: Date.now(), text, sender, action, images }]);
  };

  const handleSend = async (text: string) => {
    if (window.uploadRequiresCompletion) return;
    if (!text.trim() && !window.currentUpload) return;

    // Add user message
    addMessage(text, 'user');
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, user_id: userId })
      });
      const data = await response.json();
      setLoading(false);

      // Add bot response
      addMessage(data.text, 'bot', data.action, data.images);

      // Handle action injection
      if (data.action) {
        const { type, orderDetails, productInfo, sizes } = data.action;
        switch(type) {
          case 'showShippingModal':
            setShippingDetails(orderDetails);
            setShowShipping(true);
            break;
          case 'showProductOptions':
            setProductAction(productInfo);
            break;
          case 'showQuantitySelector':
            setQuantityAction({ sizes, onConfirm: handleQuantityConfirm });
            break;
          default:
            break;
        }
      }

      // Display images
      if (data.images) {
        data.images.forEach((img: any) => addProductImage(img.url, img.alt));
      }
    } catch (err) {
      setLoading(false);
      addMessage('Sorry, something went wrong. Please try again.', 'system');
    }
  };

  const handleQuantityConfirm = (qtys: Record<string, number>) => {
    // Send back quantities
    handleSend(JSON.stringify({ type: 'confirm_quantities', quantities: qtys }));
    setQuantityAction(null);
  };

  const handleUploadLogo = () => {
    setShowPlacement(true);
  };

  const handleFindDifferent = (msg: string) => {
    handleSend(msg);
    setProductAction(null);
  };

  const handleColorOptions = (msg: string) => {
    handleSend(msg);
    setProductAction(null);
  };

  const handleShippingCancel = () => setShowShipping(false);
  const handleShippingSubmit = (data: ShippingFormData) => {
    handleSend(JSON.stringify({ type: 'submit_shipping', ...data }));
    setShowShipping(false);
  };

  const handlePlacementSave = () => {
    // Save placement via global integration
    window.placementModal?.confirmSave?.();
    setShowPlacement(false);
  };

  const addProductImage = (url: string, alt: string) => {
    addMessage(url, 'bot');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-4">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.sender}`}> 
            {msg.sender === 'bot' && msg.loading ? <Spinner /> : msg.text}
          </div>
        ))}
        {productAction && (
          <ProductButtons
            productInfo={productAction}
            onUploadClick={handleUploadLogo}
            onFindDifferentClick={handleFindDifferent}
            onColorOptionsClick={handleColorOptions}
          />
        )}
        {quantityAction && (
          <QuantitySelector {...quantityAction} />
        )}
        <div ref={messageEndRef} />
      </div>
      <div className="border-t">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>

      {showShipping && shippingDetails && (
        <ShippingForm
          orderDetails={shippingDetails}
          onCancel={handleShippingCancel}
          onSubmit={handleShippingSubmit}
        />
      )}

      <PlacementModal
        visible={showPlacement}
        onHide={() => setShowPlacement(false)}
        onSave={handlePlacementSave}
      >
        {placementProps && (
          <DesignPlacer
            frontImage={currentProductImageUrl}
            backImage={currentProductBackImageUrl}
            designUrl={placementProps.designUrl}
            onSave={(placement) => svgBasedCompositeRenderer(placement)}
          />
        )}
      </PlacementModal>
    </div>
  );
};

export default ChatContainer;
