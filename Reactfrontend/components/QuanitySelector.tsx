// ReactFrontend/components/QuantitySelector.tsx
import React, { useState, useEffect } from 'react';
import { chatPermissions } from '../lib/chatPermissions';
import { trackFunnelStep } from '../lib/googleAnalytics';

export interface QuantitySelectorProps {
  /** Available sizes, parsed from the chatbot prompt. */
  sizes: {
    youth?: string[];
    adult?: string[];
  };
  /** Minimum total items required before proceeding (default: 24). */
  minQuantity?: number;
  /** Called when quantities are confirmed; passes a map { sizeKey: number }. */
  onConfirm: (quantities: Record<string, number>) => void;
}

const STANDARD_SIZES = ['XS', 'S', 'M', 'L', 'XL'];

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  sizes,
  minQuantity = 24,
  onConfirm,
}) => {
  const [showYouth, setShowYouth] = useState(false);
  const [showExtended, setShowExtended] = useState(false);

  const initialQuantities: Record<string, number> = {};
  (sizes.youth || []).forEach(sz => { initialQuantities[`youth_${sz}`] = 0; });
  (sizes.adult || []).forEach(sz => { initialQuantities[`adult_${sz}`] = 0; });
  const [quantities, setQuantities] = useState<Record<string, number>>(initialQuantities);

  const [error, setError] = useState<string>('');
  const total = Object.values(quantities).reduce((sum, q) => sum + q, 0);

  useEffect(() => {
    chatPermissions.disableChat('Please confirm your quantities to continue');
    return () => {
      chatPermissions.enableChat();
    };
  }, []);

  const handleIncrement = (key: string) => {
    setQuantities(q => ({ ...q, [key]: q[key] + 1 }));
  };
  const handleDecrement = (key: string) => {
    setQuantities(q => ({ ...q, [key]: Math.max(0, q[key] - 1) }));
  };

  const handleConfirm = () => {
    if (total < minQuantity) {
      setError(`Minimum quantity: ${minQuantity}`);
      return;
    }
    const summaryText = Object.entries(quantities)
      .filter(([, qty]) => qty > 0)
      .map(([key, qty]) => {
        const [type, sz] = key.split('_');
        return `${qty} ${type === 'youth' ? 'Y' : ''}${sz}`;
      })
      .join(', ');
    trackFunnelStep('quantity_selection', {
      total_quantity: total,
      submitted_quantities_text: summaryText
    });

    chatPermissions.enableChat();
    onConfirm(quantities);
  };

  const adultStandard = (sizes.adult || []).filter(sz => STANDARD_SIZES.includes(sz));
  const adultExtended = (sizes.adult || []).filter(sz => !STANDARD_SIZES.includes(sz));

  return (
    <div className="w-full mt-4 pt-4 border-t border-white/20">
      {sizes.youth?.length ? (
        <div className="mb-4">
          <div
            className="flex justify-between items-center cursor-pointer"
            onClick={() => setShowYouth(y => !y)}
          >
            <h4 className="text-sm font-medium text-[var(--secondary-color)]">
              Youth Sizes
            </h4>
            <span
              className="transform transition-transform"
              style={{ transform: showYouth ? 'rotate(0deg)' : 'rotate(-90deg)' }}
            >
              ▼
            </span>
          </div>
          {showYouth && (
            <div className="mt-2">
              {sizes.youth!.map(sz => {
                const key = `youth_${sz}`;
                return (
                  <div key={key} className="flex justify-between items-center mb-2 text-white">
                    <span className="flex-1">{sz}</span>
                    <div className="flex items-center bg-white/15 rounded overflow-hidden">
                      <button
                        onClick={() => handleDecrement(key)}
                        className="w-8 h-8 flex items-center justify-center"
                      >
                        –
                      </button>
                      <input
                        type="text"
                        readOnly
                        value={quantities[key]}
                        className="w-12 h-8 text-center bg-white/10 appearance-none"
                      />
                      <button
                        onClick={() => handleIncrement(key)}
                        className="w-8 h-8 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : null}

      {sizes.adult?.length ? (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-[var(--secondary-color)] mb-2">
            Adult Sizes
          </h4>
          <div>
            {adultStandard.map(sz => {
              const key = `adult_${sz}`;
              return (
                <div key={key} className="flex justify-between items-center mb-2 text-white">
                  <span className="flex-1">{sz}</span>
                  <div className="flex items-center bg-white/15 rounded overflow-hidden">
                    <button
                      onClick={() => handleDecrement(key)}
                      className="w-8 h-8 flex items-center justify-center"
                    >
                      –
                    </button>
                    <input
                      type="text"
                      readOnly
                      value={quantities[key]}
                      className="w-12 h-8 text-center bg-white/10 appearance-none"
                    />
                    <button
                      onClick={() => handleIncrement(key)}
                      className="w-8 h-8 flex items-center justify-center"
                    >
                      +
                    </button>
                  </div>
                </div>
              );
            })}
            {adultExtended.length > 0 && (
              <div className="mt-2">
                <button
                  onClick={() => setShowExtended(e => !e)}
                  className="text-sm text-[var(--secondary-color)] mb-2"
                >
                  {showExtended ? 'Show fewer sizes' : 'Show more sizes'}
                </button>
                {showExtended && (
                  <div className="pl-4">
                    {adultExtended.map(sz => {
                      const key = `adult_${sz}`;
                      return (
                        <div key={key} className="flex justify-between items-center mb-2 text-white">
                          <span className="flex-1">{sz}</span>
                          <div className="flex items-center bg-white/15 rounded overflow-hidden">
                            <button
                              onClick={() => handleDecrement(key)}
                              className="w-8 h-8 flex items-center justify-center"
                            >
                              –
                            </button>
                            <input
                              type="text"
                              readOnly
                              value={quantities[key]}
                              className="w-12 h-8 text-center bg-white/10 appearance-none"
                            />
                            <button
                              onClick={() => handleIncrement(key)}
                              className="w-8 h-8 flex items-center justify-center"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : null}

      <div className="flex justify-between items-center mt-4 pt-2 border-t border-white/20">
        <span className="text-sm text-white">Total: {total} items</span>
        <button
          onClick={handleConfirm}
          disabled={total === 0}
          className={
            `px-4 py-2 rounded text-sm font-medium transition-opacity ` +
            (total > 0 ? 'opacity-100' : 'opacity-50 cursor-not-allowed') +
            ' bg-[var(--primary-color)] text-white'
          }
        >
          Confirm Quantities
        </button>
      </div>
      {error && <div className="text-red-500 text-sm mt-2 text-right">{error}</div>}
    </div>
  );
};

export default QuantitySelector;