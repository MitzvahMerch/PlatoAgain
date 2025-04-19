// ReactFrontend/components/DesignPlacer.tsx
import React, { useRef, useState, useEffect } from 'react';

export interface SVGCoordinates {
  x: number;
  y: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  viewBoxWidth: number;
  viewBoxHeight: number;
}

export interface DesignPlacement {
  svgCoordinates: SVGCoordinates;
  showBackImage: boolean;
  designUrl: string;
}

export interface DesignPlacerProps {
  frontImage: string;
  backImage?: string;
  designUrl: string;
  showBackImage?: boolean;
  onSave: (placement: DesignPlacement) => void;
}

const DesignPlacer: React.FC<DesignPlacerProps> = ({
  frontImage,
  backImage,
  designUrl,
  showBackImage = false,
  onSave,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const designRef = useRef<HTMLImageElement>(null);

  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [origin, setOrigin] = useState<{ x: number; y: number } | null>(null);

  // Center the design initially
  useEffect(() => {
    const container = containerRef.current;
    const design = designRef.current;
    if (container && design) {
      const c = container.getBoundingClientRect();
      const d = design.getBoundingClientRect();
      setPosition({
        x: (c.width - d.width) / 2,
        y: (c.height - d.height) / 2,
      });
    }
  }, [designUrl]);

  const handlePointerDown = (e: React.PointerEvent) => {
    const target = e.currentTarget;
    target.setPointerCapture(e.pointerId);
    setDragging(true);
    setOrigin({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragging || !origin) return;
    setPosition({ x: e.clientX - origin.x, y: e.clientY - origin.y });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    e.currentTarget.releasePointerCapture(e.pointerId);
    setDragging(false);
    setOrigin(null);
  };

  const handleScaleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setScale(parseFloat(e.target.value));
  };

  const handleSave = () => {
    const container = containerRef.current;
    const design = designRef.current;
    if (!container || !design) return;
    const c = container.getBoundingClientRect();
    const d = design.getBoundingClientRect();
    const coords: SVGCoordinates = {
      x: (d.x - c.x) / scale,
      y: (d.y - c.y) / scale,
      width: d.width / scale,
      height: d.height / scale,
      centerX: (d.x - c.x + d.width / 2) / scale,
      centerY: (d.y - c.y + d.height / 2) / scale,
      viewBoxWidth: c.width,
      viewBoxHeight: c.height,
    };
    onSave({ svgCoordinates: coords, showBackImage, designUrl });
  };

  return (
    <div className="h-full w-full flex flex-col">
      <div
        ref={containerRef}
        className="relative flex-1 bg-gray-100 overflow-hidden rounded-lg"
      >
        <img
          src={showBackImage && backImage ? backImage : frontImage}
          alt="Product"
          className="absolute inset-0 h-full w-full object-contain"
        />

        <img
          ref={designRef}
          src={designUrl}
          alt="Design"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          style={{
            position: 'absolute',
            left: position.x,
            top: position.y,
            transform: `scale(${scale})`,
            touchAction: 'none',
            cursor: dragging ? 'grabbing' : 'grab',
          }}
        />
      </div>

      <div className="mt-4 p-2 flex items-center space-x-2">
        <label className="text-sm">Scale:</label>
        <input
          type="range"
          min="0.5"
          max="2"
          step="0.01"
          value={scale}
          onChange={handleScaleChange}
        />
      </div>

      <div className="mt-2 p-2 flex justify-end space-x-2">
        <button
          type="button"
          onClick={handleSave}
          className="px-4 py-2 bg-[var(--primary-color)] text-white rounded"
        >
          Save Placement
        </button>
      </div>
    </div>
  );
};

export default DesignPlacer;
