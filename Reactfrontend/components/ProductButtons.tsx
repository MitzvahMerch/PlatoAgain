// ReactFrontend/components/ProductButtons.tsx
import React from 'react';

export interface ProductInfo {
  name?: string;
  color?: string;
}

export interface ProductButtonsProps {
  productInfo: ProductInfo;
  onUploadClick: () => void;
  onFindDifferentClick: (message: string) => void;
  onColorOptionsClick: (message: string) => void;
}

const ProductButtons: React.FC<ProductButtonsProps> = ({
  productInfo,
  onUploadClick,
  onFindDifferentClick,
  onColorOptionsClick,
}) => {
  const handleFindDifferent = () => {
    const name = productInfo.name ?? 'product';
    const color = productInfo.color ? `The ${productInfo.color} ${name} isn’t quite right.` : '';
    const msg = color
      ? `I'd like to see a different product option. ${color}`
      : `I'd like to see a different product option.`;
    onFindDifferentClick(msg);
  };

  const handleColorOptions = () => {
    const name = productInfo.name ?? 'product';
    const msg = `Show me color options for this ${name}.`;
    onColorOptionsClick(msg);
  };

  return (
    <div className="product-buttons-container mt-4 pt-4 border-t border-gray-200 flex flex-col gap-3">
      <button
        onClick={onUploadClick}
        className="product-button upload-logo-button px-4 py-2 bg-[var(--primary-color)] text-white rounded"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="inline-block mr-2"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
        Upload Logo
      </button>

      <button
        onClick={handleColorOptions}
        className="product-button color-options-button px-4 py-2 bg-blue-600 text-white rounded"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="inline-block mr-2"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        Same Product, Different Color
      </button>

      <button
        onClick={handleFindDifferent}
        className="product-button find-product-button px-4 py-2 bg-gray-300 text-black rounded"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="inline-block mr-2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
        Find Different Product
      </button>
    </div>
  );
};

export default ProductButtons;