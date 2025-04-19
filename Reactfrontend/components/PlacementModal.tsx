// ReactFrontend/components/PlacementModal.tsx
import React, { ReactNode, useEffect } from 'react';
import { createPortal } from 'react-dom';

export interface PlacementModalProps {
  /** Whether the modal is visible */
  visible: boolean;
  /** Called when the modal is requested to hide (cancel) */
  onHide: () => void;
  /** Called when the save action is confirmed */
  onSave: () => void;
  /** Modal content, e.g., the design placer UI */
  children?: ReactNode;
}

const PlacementModal: React.FC<PlacementModalProps> = ({ visible, onHide, onSave, children }) => {
  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && visible) onHide();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [visible, onHide]);

  if (!visible) return null;

  return createPortal(
    <div className="placement-modal fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
      <div className="placement-modal-content relative w-[90%] h-[90%] bg-white rounded-2xl overflow-hidden">
        {/* Custom content */}
        {children}

        {/* Footer controls */}
        <div className="absolute bottom-4 right-4 flex space-x-2">
          <button
            type="button"
            onClick={onHide}
            className="px-4 py-2 bg-gray-200 rounded-lg text-sm font-medium"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => {
              onSave();
              onHide();
            }}
            className="px-4 py-2 bg-[var(--primary-color)] text-white rounded-lg text-sm font-medium"
          >
            Save Placement
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default PlacementModal;
