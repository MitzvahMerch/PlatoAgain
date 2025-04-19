// ReactFrontend/lib/compositeRenderer.ts

import { loadImage } from './imageLoader'; // assume you have an image loading util
import { UploadResult } from './firebase';

export interface SVGPlacement {
  svgCoordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
    centerX: number;
    centerY: number;
    viewBoxWidth: number;
    viewBoxHeight: number;
  };
  showBackImage: boolean;
  designUrl: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

export async function svgBasedCompositeRenderer(
  placement: SVGPlacement & { userId: string; currentUploadResult: UploadResult }
): Promise<void> {
  const { svgCoordinates, showBackImage, designUrl, userId, currentUploadResult } = placement;

  // Helper to convert SVG coords to actual pixels
  const originalImg = await loadImage(showBackImage ? placement.backImage : placement.frontImage);
  const designImg = await loadImage(designUrl);

  const canvas = document.createElement('canvas');
  canvas.width = originalImg.width;
  canvas.height = originalImg.height;
  const ctx = canvas.getContext('2d')!;

  ctx.drawImage(originalImg, 0, 0);

  const { x, y, width, height, centerX, centerY, viewBoxWidth, viewBoxHeight } = svgCoordinates;

  const scaleX = originalImg.width / viewBoxWidth;
  const scaleY = originalImg.height / viewBoxHeight;
  const actualWidth = width * scaleX;
  const actualHeight = height * scaleX;
  const actualCenterX = centerX * scaleX;
  const actualCenterY = centerY * scaleY;
  const actualX = actualCenterX - actualWidth / 2;
  const actualY = actualCenterY - actualHeight / 2;

  ctx.drawImage(designImg, actualX, actualY, actualWidth, actualHeight);

  const blob: Blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png')!);

  // Upload composite
  const path = currentUploadResult.path.replace(/\/[^\/]+$/, `/composite_${Date.now()}_$&`);
  const response = await fetch(`${API_BASE_URL}/api/upload-composite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: blob,
  });
  const result = await response.json();

  // Optionally show message or update state
  console.log('Composite uploaded:', result.url);
}
