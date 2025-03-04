// designPlacer.js (SVG-based implementation with improved resize handles)
const DesignPlacer = ({ frontImage, backImage, designUrl, onSave }) => {
    console.log('DesignPlacer props:', { frontImage, backImage, designUrl });
    
    // State variables
    const [showBackImage, setShowBackImage] = React.useState(false);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isResizing, setIsResizing] = React.useState(false);
    const [loadComplete, setLoadComplete] = React.useState(false);
    const [designPosition, setDesignPosition] = React.useState({ x: 0, y: 0, width: 0, height: 0 });
    
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
    
    // Start dragging the design
    const handleDragStart = React.useCallback((e) => {
        e.preventDefault();
        
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
            
            // Update position
            designRef.current.setAttribute("x", boundedX);
            designRef.current.setAttribute("y", boundedY);
            
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
                    // Only adjust width for bottom handles
                    if (currentHandleRef.current === 'sw') {
                        newX = startPositionRef.current.x + startSizeRef.current.width - newWidth;
                    }
                }
            }
            
            // Update size and position
            designRef.current.setAttribute("x", newX);
            designRef.current.setAttribute("y", newY);
            designRef.current.setAttribute("width", newWidth);
            designRef.current.setAttribute("height", newHeight);
            
            // Update state to trigger re-render for handles
            updateDesignPosition();
        }
    }, [isDragging, isResizing, screenToSVGPoint, updateDesignPosition]);
    
    // Handle mouse/touch up
    const handleMouseUp = React.useCallback(() => {
        setIsDragging(false);
        setIsResizing(false);
        currentHandleRef.current = null;
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
    
    // Create resize handles - Using designPosition state to update handle positions
    const createResizeHandles = () => {
        // Smaller handle size and closer to design edges
        const handleSize = 8; // Reduced from 10
        const { x, y, width, height } = designPosition;
        
        // Configuration for handle positions
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
            });
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
        
        return [productImage, designGroup].filter(Boolean);
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
    }, 'Drag to move, drag corners to resize');
    
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
        instructions
    ]);

    return React.StrictMode ? 
        React.createElement(React.StrictMode, null, container) : 
        container;
};

// Make available globally
window.DesignPlacer = DesignPlacer;