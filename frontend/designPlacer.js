// designPlacer.js (SVG-based implementation with improved resize handles, centering guides, and mobile support)
const DesignPlacer = ({ frontImage, backImage, designUrl, onSave }) => {
    console.log('DesignPlacer props:', { frontImage, backImage, designUrl });

    // State variables
    const [showBackImage, setShowBackImage] = React.useState(false);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isResizing, setIsResizing] = React.useState(false);
    const [loadComplete, setLoadComplete] = React.useState(false);
    const [designPosition, setDesignPosition] = React.useState({ x: 0, y: 0, width: 0, height: 0 });
    const [showCenterGuide, setShowCenterGuide] = React.useState({ vertical: false, horizontal: false });
    // New mobile detection state
    const [isMobile, setIsMobile] = React.useState(false);

    // SVG viewBox dimensions
    const SVG_WIDTH = 1000;
    const [SVG_HEIGHT, setSVGHeight] = React.useState(1000);

    // References
    const svgRef = React.useRef(null);
    const designRef = React.useRef(null);
    const productImageRef = React.useRef(null);
    const startPosRef = React.useRef({ x: 0, y: 0 });
    const startPositionRef = React.useRef({ x: 0, y: 0 });
    const startSizeRef = React.useRef({ width: 0, height: 0 });
    const currentHandleRef = React.useRef(null);

    // Detect mobile devices on component mount
    React.useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth <= 768 ||
                           ('ontouchstart' in window) ||
                           (navigator.maxTouchPoints > 0);
            setIsMobile(mobile);
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);

        return () => {
            window.removeEventListener('resize', checkMobile);
        };
    }, []);

    // Initialize SVG dimensions based on product image aspect ratio
    React.useEffect(() => {
        if (frontImage) {
            const img = new Image();
            img.onload = () => {
                const aspectRatio = img.height / img.width;
                setSVGHeight(1000 * aspectRatio);
                if (svgRef.current) {
                    svgRef.current.setAttribute('viewBox', `0 0 ${SVG_WIDTH} ${1000 * aspectRatio}`);
                }
            };
            img.src = frontImage;
        }
    }, [frontImage]);

    // Update design position state whenever the design element attributes change
    const updateDesignPosition = React.useCallback(() => {
        if (designRef.current) {
            const x = parseFloat(designRef.current.getAttribute("x")) || 0;
            const y = parseFloat(designRef.current.getAttribute("y")) || 0;
            const width = parseFloat(designRef.current.getAttribute("width")) || 0;
            const height = parseFloat(designRef.current.getAttribute("height")) || 0;

            setDesignPosition({ x, y, width, height });
        }
    }, []);

    // Initialize design position and size
    React.useEffect(() => {
        if (designUrl && svgRef.current) {
            const img = new Image();
            img.onload = () => {
                const aspectRatio = img.height / img.width;

                // Calculate initial design size (20% of SVG width)
                const initialWidth = SVG_WIDTH * 0.2;
                const initialHeight = initialWidth * aspectRatio;

                // Position in the center
                const initialX = (SVG_WIDTH - initialWidth) / 2;
                const initialY = (SVG_HEIGHT - initialHeight) / 2;

                if (!designRef.current && svgRef.current) {
                    const designImage = document.createElementNS("http://www.w3.org/2000/svg", "image");
                    designImage.setAttribute("id", "design-image");
                    designImage.setAttribute("href", designUrl);
                    designImage.setAttribute("x", initialX);
                    designImage.setAttribute("y", initialY);
                    designImage.setAttribute("width", initialWidth);
                    designImage.setAttribute("height", initialHeight);
                    designImage.setAttribute("preserveAspectRatio", "xMidYMid meet");

                    // For desktop
                    designImage.addEventListener('mousedown', handleDragStart);
                    // For mobile – use the new touch handler
                    designImage.addEventListener('touchstart', handleTouchStart, { passive: false });

                    svgRef.current.appendChild(designImage);
                    designRef.current = designImage;

                    setDesignPosition({
                        x: initialX,
                        y: initialY,
                        width: initialWidth,
                        height: initialHeight
                    });

                    setLoadComplete(true);
                }
            };
            img.src = designUrl;
        }
    }, [designUrl, svgRef.current]);

    // Convert screen coordinates to SVG coordinates
    const screenToSVGPoint = React.useCallback((screenX, screenY) => {
        if (!svgRef.current) return { x: 0, y: 0 };

        const svgElement = svgRef.current;
        const pt = svgElement.createSVGPoint();
        pt.x = screenX;
        pt.y = screenY;

        return pt.matrixTransform(svgElement.getScreenCTM().inverse());
    }, []);

    // Start dragging the design
    const handleDragStart = React.useCallback((e) => {
        e.preventDefault();
        if (!designRef.current) return;

        setIsDragging(true);

        // Get current design position
        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        startPositionRef.current = { x, y };

        // Store mouse start position
        const svgPoint = screenToSVGPoint(e.clientX, e.clientY);
        startPosRef.current = svgPoint;

        console.log('Drag start:', { position: startPositionRef.current, mouse: startPosRef.current });
    }, [screenToSVGPoint]);

    // Start resizing the design
    const handleResizeStart = React.useCallback((e, handle) => {
        e.preventDefault();
        e.stopPropagation();
        if (!designRef.current) return;

        setIsResizing(true);
        currentHandleRef.current = handle;

        // Get current design position and size
        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        const width = parseFloat(designRef.current.getAttribute("width")) || 0;
        const height = parseFloat(designRef.current.getAttribute("height")) || 0;

        startPositionRef.current = { x, y };
        startSizeRef.current = { width, height };

        // Store mouse start position
        const svgPoint = screenToSVGPoint(e.clientX, e.clientY);
        startPosRef.current = svgPoint;

        console.log('Resize start:', { 
            position: startPositionRef.current, 
            size: startSizeRef.current, 
            mouse: startPosRef.current,
            handle
        });
    }, [screenToSVGPoint]);

    // Check if design is close to center and show guides
    const checkCenterAlignment = React.useCallback((x, y, width, height) => {
        const designCenterX = x + (width / 2);
        const designCenterY = y + (height / 2);
        const canvasCenterX = SVG_WIDTH / 2;
        const canvasCenterY = SVG_HEIGHT / 2;

        // Snap threshold – 2% of canvas width
        const snapThreshold = SVG_WIDTH * 0.02;

        let newX = x;
        let newY = y;
        let verticalGuide = false;
        let horizontalGuide = false;

        if (Math.abs(designCenterX - canvasCenterX) < snapThreshold) {
            newX = canvasCenterX - (width / 2);
            verticalGuide = true;
        }
        if (Math.abs(designCenterY - canvasCenterY) < snapThreshold) {
            newY = canvasCenterY - (height / 2);
            horizontalGuide = true;
        }

        setShowCenterGuide({ vertical: verticalGuide, horizontal: horizontalGuide });

        return { newX, newY, isAligned: verticalGuide || horizontalGuide };
    }, [SVG_WIDTH, SVG_HEIGHT]);

    // -- Mobile resize function and touch handlers --

    // Handle mobile resize via slider
    const handleMobileResize = React.useCallback((sizePercent) => {
        if (!designRef.current) return;

        const originalWidth = parseFloat(designRef.current.getAttribute("width"));
        const originalHeight = parseFloat(designRef.current.getAttribute("height"));
        const aspectRatio = originalHeight / originalWidth;

        const newWidth = SVG_WIDTH * (sizePercent / 100);
        const newHeight = newWidth * aspectRatio;

        const oldX = parseFloat(designRef.current.getAttribute("x"));
        const oldY = parseFloat(designRef.current.getAttribute("y"));
        const oldCenterX = oldX + (originalWidth / 2);
        const oldCenterY = oldY + (originalHeight / 2);

        const newX = oldCenterX - (newWidth / 2);
        const newY = oldCenterY - (newHeight / 2);

        const boundedX = Math.max(0, Math.min(SVG_WIDTH - newWidth, newX));
        const boundedY = Math.max(0, Math.min(SVG_HEIGHT - newHeight, newY));

        const { newX: alignedX, newY: alignedY } = checkCenterAlignment(boundedX, boundedY, newWidth, newHeight);

        designRef.current.setAttribute("x", alignedX);
        designRef.current.setAttribute("y", alignedY);
        designRef.current.setAttribute("width", newWidth);
        designRef.current.setAttribute("height", newHeight);

        updateDesignPosition();
    }, [checkCenterAlignment, updateDesignPosition]);

    // Improved touch handling for drag – touch start
    const handleTouchStart = React.useCallback((e) => {
        if (!designRef.current) return;

        e.preventDefault();
        const touch = e.touches[0];

        setIsDragging(true);

        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        startPositionRef.current = { x, y };

        const svgPoint = screenToSVGPoint(touch.clientX, touch.clientY);
        startPosRef.current = svgPoint;
    }, [screenToSVGPoint]);

    // Handle touch move
    const handleTouchMove = React.useCallback((e) => {
        if (!isDragging || !designRef.current) return;

        const touch = e.touches[0];
        const currentPoint = screenToSVGPoint(touch.clientX, touch.clientY);
        const dx = currentPoint.x - startPosRef.current.x;
        const dy = currentPoint.y - startPosRef.current.y;

        const newX = startPositionRef.current.x + dx;
        const newY = startPositionRef.current.y + dy;

        const width = parseFloat(designRef.current.getAttribute("width")) || 0;
        const height = parseFloat(designRef.current.getAttribute("height")) || 0;

        const boundedX = Math.max(0, Math.min(SVG_WIDTH - width, newX));
        const boundedY = Math.max(0, Math.min(SVG_HEIGHT - height, newY));

        const { newX: alignedX, newY: alignedY } = checkCenterAlignment(boundedX, boundedY, width, height);

        designRef.current.setAttribute("x", alignedX);
        designRef.current.setAttribute("y", alignedY);

        updateDesignPosition();
    }, [isDragging, screenToSVGPoint, checkCenterAlignment, updateDesignPosition]);

    // Handle mouse/touch move for drag and resize
    const handleMouseMove = React.useCallback((e) => {
        if (!isDragging && !isResizing) return;
        if (!designRef.current) return;

        const currentPoint = screenToSVGPoint(e.clientX, e.clientY);
        const dx = currentPoint.x - startPosRef.current.x;
        const dy = currentPoint.y - startPosRef.current.y;

        if (isDragging) {
            const newX = startPositionRef.current.x + dx;
            const newY = startPositionRef.current.y + dy;

            const width = parseFloat(designRef.current.getAttribute("width")) || 0;
            const height = parseFloat(designRef.current.getAttribute("height")) || 0;

            const boundedX = Math.max(0, Math.min(SVG_WIDTH - width, newX));
            const boundedY = Math.max(0, Math.min(SVG_HEIGHT - height, newY));

            const { newX: alignedX, newY: alignedY } = checkCenterAlignment(boundedX, boundedY, width, height);

            designRef.current.setAttribute("x", alignedX);
            designRef.current.setAttribute("y", alignedY);

            updateDesignPosition();
        } else if (isResizing) {
            const aspectRatio = startSizeRef.current.height / startSizeRef.current.width;
            let newWidth = startSizeRef.current.width;
            let newHeight = startSizeRef.current.height;
            let newX = startPositionRef.current.x;
            let newY = startPositionRef.current.y;

            switch (currentHandleRef.current) {
                case 'se': // Bottom right
                    newWidth = startSizeRef.current.width + dx;
                    newHeight = newWidth * aspectRatio;
                    break;
                case 'sw': // Bottom left
                    newWidth = startSizeRef.current.width - dx;
                    newHeight = newWidth * aspectRatio;
                    newX = startPositionRef.current.x + dx;
                    break;
                case 'ne': // Top right
                    newWidth = startSizeRef.current.width + dx;
                    newHeight = newWidth * aspectRatio;
                    newY = startPositionRef.current.y + startSizeRef.current.height - newHeight;
                    break;
                case 'nw': // Top left
                    newWidth = startSizeRef.current.width - dx;
                    newHeight = newWidth * aspectRatio;
                    newX = startPositionRef.current.x + dx;
                    newY = startPositionRef.current.y + startSizeRef.current.height - newHeight;
                    break;
            }

            const minSize = SVG_WIDTH * 0.03;
            if (newWidth < minSize) {
                newWidth = minSize;
                newHeight = newWidth * aspectRatio;
                if (currentHandleRef.current === 'sw' || currentHandleRef.current === 'nw') {
                    newX = startPositionRef.current.x + startSizeRef.current.width - newWidth;
                }
                if (currentHandleRef.current === 'nw' || currentHandleRef.current === 'ne') {
                    newY = startPositionRef.current.y + startSizeRef.current.height - newHeight;
                }
            }

            if (newX < 0) {
                newX = 0;
                newWidth = startPositionRef.current.x + startSizeRef.current.width;
                newHeight = newWidth * aspectRatio;
            }
            if (newY < 0) {
                newY = 0;
                newHeight = startPositionRef.current.y + startSizeRef.current.height;
                newWidth = newHeight / aspectRatio;
                if (currentHandleRef.current === 'nw' || currentHandleRef.current === 'sw') {
                    newX = startPositionRef.current.x + startSizeRef.current.width - newWidth;
                }
            }
            if (newX + newWidth > SVG_WIDTH) {
                newWidth = SVG_WIDTH - newX;
                newHeight = newWidth * aspectRatio;
            }
            if (newY + newHeight > SVG_HEIGHT) {
                newHeight = SVG_HEIGHT - newY;
                newWidth = newHeight / aspectRatio;
                if (currentHandleRef.current === 'sw' || currentHandleRef.current === 'se') {
                    if (currentHandleRef.current === 'sw') {
                        newX = startPositionRef.current.x + startSizeRef.current.width - newWidth;
                    }
                }
            }

            const { newX: alignedX, newY: alignedY } = checkCenterAlignment(newX, newY, newWidth, newHeight);

            designRef.current.setAttribute("x", alignedX);
            designRef.current.setAttribute("y", alignedY);
            designRef.current.setAttribute("width", newWidth);
            designRef.current.setAttribute("height", newHeight);

            updateDesignPosition();
        }
    }, [isDragging, isResizing, screenToSVGPoint, updateDesignPosition, checkCenterAlignment]);

    // Handle mouse/touch up
    const handleMouseUp = React.useCallback(() => {
        setIsDragging(false);
        setIsResizing(false);
        currentHandleRef.current = null;

        setTimeout(() => {
            setShowCenterGuide({ vertical: false, horizontal: false });
        }, 500);
    }, []);

    // -- Modify event listeners --
    React.useEffect(() => {
        // Mouse events for desktop
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);

        // Touch events for mobile
        window.addEventListener('touchmove', handleTouchMove, { passive: false });
        window.addEventListener('touchend', handleMouseUp);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            window.removeEventListener('touchmove', handleTouchMove);
            window.removeEventListener('touchend', handleMouseUp);
        };
    }, [handleMouseMove, handleMouseUp, handleTouchMove]);

    // Save the placement by capturing the SVG coordinates
    // Save the placement by capturing the SVG coordinates
// Only modify the handleSave function in designPlacer.js
// This is the function that needs to be updated

const handleSave = () => {
    if (!designRef.current || !svgRef.current || !productImageRef.current) {
        console.error('Required elements not found');
        return;
    }
    
    // Find the save button element and disable it immediately
    const saveButtonElement = document.querySelector('[style*="background-color: #28a745"]');
    if (saveButtonElement) {
        // Change appearance to indicate disabled state
        saveButtonElement.style.backgroundColor = '#6c757d';
        saveButtonElement.style.cursor = 'not-allowed';
        saveButtonElement.disabled = true;
        // Optionally change text to indicate processing
        saveButtonElement.textContent = 'Saving...';
    }

    const x = parseFloat(designRef.current.getAttribute("x"));
    const y = parseFloat(designRef.current.getAttribute("y"));
    const width = parseFloat(designRef.current.getAttribute("width"));
    const height = parseFloat(designRef.current.getAttribute("height"));

    const centerX = x + (width / 2);
    const centerY = y + (height / 2);

    const centerXPercent = centerX / SVG_WIDTH;
    const centerYPercent = centerY / SVG_HEIGHT;
    const widthPercent = width / SVG_WIDTH;
    const heightPercent = height / SVG_HEIGHT;

    console.log('Saving placement:', {
        svgCoordinates: { x, y, width, height },
        center: { x: centerX, y: centerY },
        percentages: {
            centerX: centerXPercent,
            centerY: centerYPercent,
            width: widthPercent,
            height: heightPercent
        }
    });

    // Call the provided onSave callback with the SVG data
    onSave?.({
        svgCoordinates: {
            x, y, width, height,
            centerX, centerY,
            viewBoxWidth: SVG_WIDTH,
            viewBoxHeight: SVG_HEIGHT
        },
        showBackImage,
        designUrl
    });
    
    // ADDED: Trigger callback to hide design options once design is placed
    if (typeof window.onDesignPlacementSaved === 'function') {
        console.log('Calling onDesignPlacementSaved callback');
        window.onDesignPlacementSaved();
    }
    
    // We don't need to re-enable the button since the whole component 
    // will be unmounted or replaced after the save operation completes
};

    // -- Create resize handles (desktop only) --
    const createResizeHandles = () => {
        if (isMobile) return []; // Don't show resize handles on mobile

        const handleSize = 8; // Reduced from 10
        const { x, y, width, height } = designPosition;
        const handles = [
            { position: 'nw', cursor: 'nwse-resize', cx: x, cy: y },
            { position: 'ne', cursor: 'nesw-resize', cx: x + width, cy: y },
            { position: 'se', cursor: 'nwse-resize', cx: x + width, cy: y + height },
            { position: 'sw', cursor: 'nesw-resize', cx: x, cy: y + height }
        ];

        return handles.map(handle => {
            return React.createElement('circle', {
                key: handle.position,
                cx: handle.cx,
                cy: handle.cy,
                r: handleSize,
                fill: 'white',
                stroke: '#0066ff',
                strokeWidth: 2,
                style: { cursor: handle.cursor },
                onMouseDown: (e) => handleResizeStart(e, handle.position)
            });
        });
    };

    // -- Create mobile resize controls above the canvas --
    const createMobileResizeControls = () => {
        if (!isMobile || !loadComplete) return null;

        const sliderContainerStyle = {
            position: 'absolute',
            top: '0',
            left: '0',
            width: '100%',
            padding: '10px',
            backgroundColor: '#f0f0f0',
            borderBottom: '1px solid #ccc',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            zIndex: 3000
        };

        const currentSize = Math.round((designPosition.width / SVG_WIDTH) * 100);

        return React.createElement('div', { style: sliderContainerStyle }, [
            React.createElement('div', { 
                key: 'slider-label',
                style: { color: '#333', marginBottom: '5px', fontWeight: 'bold' }
            }, `Design Size: ${currentSize}%`),
            React.createElement('input', {
                key: 'size-slider',
                type: 'range',
                min: 5,
                max: 70,
                value: currentSize,
                onChange: (e) => handleMobileResize(parseInt(e.target.value)),
                style: { width: '90%' }
            })
        ]);
    };

    // Create SVG elements for the editor
    const createSVGElements = () => {
        const productImage = React.createElement('image', {
            key: 'product-image',
            ref: productImageRef,
            href: showBackImage ? backImage : frontImage,
            x: 0,
            y: 0,
            width: SVG_WIDTH,
            height: SVG_HEIGHT,
            preserveAspectRatio: "xMidYMid meet"
        });

        const centerGuides = [];

        if (showCenterGuide.vertical) {
            centerGuides.push(
                React.createElement('line', {
                    key: 'vertical-guide',
                    x1: SVG_WIDTH / 2,
                    y1: 0,
                    x2: SVG_WIDTH / 2,
                    y2: SVG_HEIGHT,
                    stroke: '#ff3366',
                    strokeWidth: 2,
                    strokeDasharray: '10,5',
                    opacity: 0.8
                })
            );
        }

        if (showCenterGuide.horizontal) {
            centerGuides.push(
                React.createElement('line', {
                    key: 'horizontal-guide',
                    x1: 0,
                    y1: SVG_HEIGHT / 2,
                    x2: SVG_WIDTH,
                    y2: SVG_HEIGHT / 2,
                    stroke: '#ff3366',
                    strokeWidth: 2,
                    strokeDasharray: '10,5',
                    opacity: 0.8
                })
            );
        }

        // Create design container group for drag operations (updated touch handling)
        const designGroup = loadComplete ? React.createElement('g', {
            key: 'design-group',
            onMouseDown: handleDragStart,
            onTouchStart: handleTouchStart,
            style: { cursor: isDragging ? 'grabbing' : 'grab' }
        }, [
            ...createResizeHandles() // Will be empty on mobile
        ]) : null;

        return [productImage, ...centerGuides, designGroup].filter(Boolean);
    };

    // Main SVG container
    const svgContainer = React.createElement('svg', {
        ref: svgRef,
        viewBox: `0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`,
        preserveAspectRatio: "xMidYMid meet",
        style: {
            width: '100%',
            height: '100%',
            backgroundColor: '#f0f0f0'
        }
    }, createSVGElements());

    // Toggle button
    const toggleButton = React.createElement('button', {
        onClick: () => {
            console.log('Toggle clicked, switching from', showBackImage ? 'back' : 'front', 
                        'to', showBackImage ? 'front' : 'back');
            setShowBackImage(!showBackImage);
        },
        style: {
            position: 'absolute',
            bottom: '20px',
            left: '20px',
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 3000
        }
    }, showBackImage ? 'Front' : 'Back');

    // Save button
    const saveButton = React.createElement('button', {
        onClick: handleSave,
        style: {
            position: 'absolute',
            bottom: '20px',
            right: '20px',
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 3000
        }
    }, 'Save Placement');

    // Close button
    const closeButton = React.createElement('button', {
        onClick: () => {
            window.placementModal.hide();
            const fileInput = document.getElementById('image-upload');
            if (fileInput) fileInput.value = '';
            const uploadButton = document.querySelector('.chat-upload-button svg');
            if (uploadButton) {
                uploadButton.innerHTML = `
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                `;
                uploadButton.style.color = 'var(--secondary-color)';
            }
        },
        style: {
            position: 'absolute',
            top: '10px',
            right: '10px',
            padding: '5px 10px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 3000
        }
    }, 'X');

    // Main container with adjusted layout for mobile
    const container = React.createElement('div', {
        style: {
            position: 'relative',
            width: '100%',
            height: '600px',
            overflow: 'hidden'
        }
    }, [
        // Include mobile resize controls at the top
        createMobileResizeControls(),
        // SVG wrapper with adjusted height/position on mobile
        React.createElement('div', {
            style: {
                position: 'relative',
                width: '100%',
                height: isMobile ? '540px' : '600px',
                marginTop: isMobile ? '60px' : '0',
                overflow: 'hidden'
            }
        }, [
            svgContainer,
            // Show different instructions based on device type
            React.createElement('div', {
                style: {
                    position: 'absolute',
                    top: '20px',
                    left: '20px',
                    padding: '10px',
                    backgroundColor: 'rgba(0,0,0,0.7)',
                    color: 'white',
                    borderRadius: '4px',
                    zIndex: 3000,
                    fontSize: '14px'
                }
            }, isMobile ? 'Drag to move design' : 'Drag to move, drag corners to resize'),
        ]),
        toggleButton,
        saveButton,
        closeButton
    ]);

    return React.StrictMode ?
        React.createElement(React.StrictMode, null, container) :
        container;
};

// Make available globally
window.DesignPlacer = DesignPlacer;