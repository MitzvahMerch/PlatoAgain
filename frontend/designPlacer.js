// designPlacer.js (SVG-based implementation with improved mobile support for resize handles and centering guides)
const DesignPlacer = ({ frontImage, backImage, designUrl, onSave }) => {
    console.log('DesignPlacer props:', { frontImage, backImage, designUrl });
    
    // State variables
    const [showBackImage, setShowBackImage] = React.useState(false);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isResizing, setIsResizing] = React.useState(false);
    const [loadComplete, setLoadComplete] = React.useState(false);
    const [designPosition, setDesignPosition] = React.useState({ x: 0, y: 0, width: 0, height: 0 });
    const [showCenterGuide, setShowCenterGuide] = React.useState({ vertical: false, horizontal: false });
    
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
    
    // Utility: Detect mobile devices
    const isMobileDevice = /Mobi|Android/i.test(navigator.userAgent);
    
    // Initialize SVG dimensions based on product image aspect ratio
    React.useEffect(() => {
        if (frontImage) {
            // Get product image natural dimensions
            const img = new Image();
            img.onload = () => {
                const aspectRatio = img.height / img.width;
                // Update SVG_HEIGHT based on aspect ratio
                setSVGHeight(1000 * aspectRatio);
                
                // If SVG ref is already available, update viewBox
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
            // Load design image to get dimensions
            const img = new Image();
            img.onload = () => {
                const aspectRatio = img.height / img.width;
                
                // Calculate initial design size (20% of SVG width)
                const initialWidth = SVG_WIDTH * 0.2;
                const initialHeight = initialWidth * aspectRatio;
                
                // Position in the center
                const initialX = (SVG_WIDTH - initialWidth) / 2;
                const initialY = (SVG_HEIGHT - initialHeight) / 2;
                
                // Create design element if it doesn't exist
                if (!designRef.current && svgRef.current) {
                    const designImage = document.createElementNS("http://www.w3.org/2000/svg", "image");
                    designImage.setAttribute("id", "design-image");
                    designImage.setAttribute("href", designUrl);
                    designImage.setAttribute("x", initialX);
                    designImage.setAttribute("y", initialY);
                    designImage.setAttribute("width", initialWidth);
                    designImage.setAttribute("height", initialHeight);
                    designImage.setAttribute("preserveAspectRatio", "xMidYMid meet");

                    // Add event listeners for dragging
                    designImage.addEventListener('mousedown', handleDragStart);
                    designImage.addEventListener('touchstart', (e) => {
                        e.preventDefault();
                        const touch = e.touches[0];
                        handleDragStart({
                            clientX: touch.clientX,
                            clientY: touch.clientY,
                            preventDefault: () => {}
                        });
                    });
                    
                    svgRef.current.appendChild(designImage);
                    designRef.current = designImage;
                    
                    // Update design position state
                    setDesignPosition({
                        x: initialX,
                        y: initialY,
                        width: initialWidth,
                        height: initialHeight
                    });
                    
                    // Now that we have loaded both the product and design
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
    
    // Start dragging the design. On mobile, ignore drag events originating from the resize handle.
    const handleDragStart = React.useCallback((e) => {
        e.preventDefault();
        if (isMobileDevice && e.target.tagName.toLowerCase() === 'circle') return;
        
        if (!designRef.current) return;
        
        setIsDragging(true);
        
        // Get current design position
        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        
        // Store start position
        startPositionRef.current = { x, y };
        
        // Store mouse start position
        const svgPoint = screenToSVGPoint(e.clientX, e.clientY);
        startPosRef.current = svgPoint;
        
        console.log('Drag start:', { position: startPositionRef.current, mouse: startPosRef.current });
    }, [screenToSVGPoint, isMobileDevice]);
    
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
        
        // Store start values
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
        // Calculate center points
        const designCenterX = x + (width / 2);
        const designCenterY = y + (height / 2);
        const canvasCenterX = SVG_WIDTH / 2;
        const canvasCenterY = SVG_HEIGHT / 2;
        
        // Snap threshold - how close the design needs to be to snap to center (in SVG units)
        const snapThreshold = SVG_WIDTH * 0.02; // 2% of canvas width
        
        let newX = x;
        let newY = y;
        let verticalGuide = false;
        let horizontalGuide = false;
        
        // Check vertical centering
        if (Math.abs(designCenterX - canvasCenterX) < snapThreshold) {
            // Snap to center
            newX = canvasCenterX - (width / 2);
            verticalGuide = true;
        }
        
        // Check horizontal centering
        if (Math.abs(designCenterY - canvasCenterY) < snapThreshold) {
            // Snap to center
            newY = canvasCenterY - (height / 2);
            horizontalGuide = true;
        }
        
        // Update guides state
        setShowCenterGuide({ vertical: verticalGuide, horizontal: horizontalGuide });
        
        return { newX, newY, isAligned: verticalGuide || horizontalGuide };
    }, [SVG_WIDTH, SVG_HEIGHT]);
    
    // Handle mouse/touch move for drag and resize
    const handleMouseMove = React.useCallback((e) => {
        if (!isDragging && !isResizing) return;
        if (!designRef.current) return;
        
        // Current mouse position in SVG coordinates
        const currentPoint = screenToSVGPoint(e.clientX, e.clientY);
        const dx = currentPoint.x - startPosRef.current.x;
        const dy = currentPoint.y - startPosRef.current.y;
        
        if (isDragging) {
            // Calculate new position
            const newX = startPositionRef.current.x + dx;
            const newY = startPositionRef.current.y + dy;
            
            // Apply bounds checking
            const width = parseFloat(designRef.current.getAttribute("width")) || 0;
            const height = parseFloat(designRef.current.getAttribute("height")) || 0;
            
            const boundedX = Math.max(0, Math.min(SVG_WIDTH - width, newX));
            const boundedY = Math.max(0, Math.min(SVG_HEIGHT - height, newY));
            
            // Check for center alignment and potentially snap
            const { newX: alignedX, newY: alignedY } = checkCenterAlignment(boundedX, boundedY, width, height);
            
            // Update position
            designRef.current.setAttribute("x", alignedX);
            designRef.current.setAttribute("y", alignedY);
            
            // Update state to trigger re-render for handles
            updateDesignPosition();
        } 
        else if (isResizing) {
            // Get current aspect ratio
            const aspectRatio = startSizeRef.current.height / startSizeRef.current.width;
            
            // New dimensions will depend on which handle is being dragged
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
                case 'ne': // Top right (mobile uses only this handle)
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
            
            // Ensure minimum size (3% of SVG)
            const minSize = SVG_WIDTH * 0.03;
            if (newWidth < minSize) {
                newWidth = minSize;
                newHeight = newWidth * aspectRatio;
                
                // Adjust position based on which handle is being used
                if (currentHandleRef.current === 'sw' || currentHandleRef.current === 'nw') {
                    newX = startPositionRef.current.x + startSizeRef.current.width - newWidth;
                }
                if (currentHandleRef.current === 'nw' || currentHandleRef.current === 'ne') {
                    newY = startPositionRef.current.y + startSizeRef.current.height - newHeight;
                }
            }
            
            // Ensure design stays within SVG bounds
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
            
            // Check for center alignment during resize
            const { newX: alignedX, newY: alignedY } = checkCenterAlignment(newX, newY, newWidth, newHeight);
            
            // Update size and position
            designRef.current.setAttribute("x", alignedX);
            designRef.current.setAttribute("y", alignedY);
            designRef.current.setAttribute("width", newWidth);
            designRef.current.setAttribute("height", newHeight);
            
            // Update state to trigger re-render for handles
            updateDesignPosition();
        }
    }, [isDragging, isResizing, screenToSVGPoint, updateDesignPosition, checkCenterAlignment]);
    
    // Handle mouse/touch up
    const handleMouseUp = React.useCallback(() => {
        setIsDragging(false);
        setIsResizing(false);
        currentHandleRef.current = null;
        
        // Clear guides after a brief delay to not have them disappear instantly
        setTimeout(() => {
            setShowCenterGuide({ vertical: false, horizontal: false });
        }, 500);
    }, []);
    
    // Add/remove event listeners
    React.useEffect(() => {
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        window.addEventListener('touchmove', e => {
            const touch = e.touches[0];
            handleMouseMove({
                clientX: touch.clientX,
                clientY: touch.clientY,
                preventDefault: () => e.preventDefault()
            });
        });
        window.addEventListener('touchend', handleMouseUp);
        
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            window.removeEventListener('touchmove', handleMouseMove);
            window.removeEventListener('touchend', handleMouseUp);
        };
    }, [handleMouseMove, handleMouseUp]);
    
    // Save the placement by capturing the SVG coordinates
    const handleSave = () => {
        if (!designRef.current || !svgRef.current || !productImageRef.current) {
            console.error('Required elements not found');
            return;
        }
        
        // Get exact SVG positions and dimensions
        const x = parseFloat(designRef.current.getAttribute("x"));
        const y = parseFloat(designRef.current.getAttribute("y"));
        const width = parseFloat(designRef.current.getAttribute("width"));
        const height = parseFloat(designRef.current.getAttribute("height"));
        
        // Calculate center point
        const centerX = x + (width / 2);
        const centerY = y + (height / 2);
        
        // Calculate position as percentage of SVG dimensions (for reference)
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
    };
    
    // Create resize handles - using designPosition state to update handle positions
    const createResizeHandles = () => {
        // On mobile, we show only one larger handle at the top right ("ne") for resizing.
        const isMobile = isMobileDevice;
        const handleSize = isMobile ? 24 : 8;
        const hitAreaSize = isMobile ? 32 : handleSize;
        const { x, y, width, height } = designPosition;
        
        let handles;
        if (isMobile) {
            // Only one handle (top right) on mobile
            handles = [{ position: 'ne', cursor: 'nesw-resize', cx: x + width, cy: y }];
        } else {
            // All four handles on desktop
            handles = [
                { position: 'nw', cursor: 'nwse-resize', cx: x,         cy: y },
                { position: 'ne', cursor: 'nesw-resize', cx: x + width, cy: y },
                { position: 'se', cursor: 'nwse-resize', cx: x + width, cy: y + height },
                { position: 'sw', cursor: 'nesw-resize', cx: x,         cy: y + height }
            ];
        }
        
        return handles.map(handle => {
            return React.createElement('g', { key: handle.position },
                // Invisible hit area to boost touch target
                React.createElement('circle', {
                    cx: handle.cx,
                    cy: handle.cy,
                    r: hitAreaSize,
                    fill: 'transparent',
                    onMouseDown: (e) => handleResizeStart(e, handle.position),
                    onTouchStart: (e) => {
                        e.preventDefault();
                        const touch = e.touches[0];
                        handleResizeStart({
                            clientX: touch.clientX,
                            clientY: touch.clientY,
                            preventDefault: () => {},
                            stopPropagation: () => {}
                        }, handle.position);
                    }
                }),
                // Visible handle
                React.createElement('circle', {
                    cx: handle.cx,
                    cy: handle.cy,
                    r: handleSize,
                    fill: 'white',
                    stroke: '#0066ff',
                    strokeWidth: 2,
                    style: { cursor: handle.cursor },
                    onMouseDown: (e) => handleResizeStart(e, handle.position),
                    onTouchStart: (e) => {
                        e.preventDefault();
                        const touch = e.touches[0];
                        handleResizeStart({
                            clientX: touch.clientX,
                            clientY: touch.clientY,
                            preventDefault: () => {},
                            stopPropagation: () => {}
                        }, handle.position);
                    }
                })
            );
        });
    };
    
    // Create SVG elements for the editor
    const createSVGElements = () => {
        // Create product image element
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
        
        // Create center alignment guides
        const centerGuides = [];
        
        // Vertical center guide
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
        
        // Horizontal center guide
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
        
        // Create design container group for drag operations
        const designGroup = loadComplete ? React.createElement('g', {
            key: 'design-group',
            onMouseDown: handleDragStart,
            onTouchStart: (e) => {
                e.preventDefault();
                const touch = e.touches[0];
                handleDragStart({
                    clientX: touch.clientX,
                    clientY: touch.clientY,
                    preventDefault: () => {}
                });
            },
            style: { cursor: isDragging ? 'grabbing' : 'grab' }
        }, [
            // Add resize handles
            ...createResizeHandles()
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
    }, showBackImage ? 'Show Front' : 'Show Back');
    
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
    
    // Instructions
    const instructions = React.createElement('div', {
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
    }, 'Drag to move, drag corner to resize');
    
    // Close button
    const closeButton = React.createElement('button', {
        onClick: () => {
            window.placementModal.hide();
            // Reset the file input
            const fileInput = document.getElementById('image-upload');
            if (fileInput) fileInput.value = '';
            // Reset upload button appearance
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
    
    // Main container
    const container = React.createElement('div', {
        style: {
            position: 'relative',
            width: '100%',
            height: '600px',
            overflow: 'hidden'
        }
    }, [
        svgContainer,
        saveButton,
        toggleButton,
        instructions,
        closeButton
    ]);

    return React.StrictMode ? 
        React.createElement(React.StrictMode, null, container) : 
        container;
};

// Make available globally
window.DesignPlacer = DesignPlacer;