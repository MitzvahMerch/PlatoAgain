// designPlacer.js (SVG-based implementation with improved resize handles and centering guides)
const DesignPlacer = ({ frontImage, backImage, designUrl, onSave }) => {
    console.log('DesignPlacer props:', { frontImage, backImage, designUrl });

    // State variables
    const [showBackImage, setShowBackImage] = React.useState(false);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isResizing, setIsResizing] = React.useState(false);
    const [loadComplete, setLoadComplete] = React.useState(false);
    const [designPosition, setDesignPosition] = React.useState({ x: 0, y: 0, width: 0, height: 0 });
    const [showCenterGuide, setShowCenterGuide] = React.useState({ vertical: false, horizontal: false });
    // New state variables for mobile detection and resize controls
    const [isMobile, setIsMobile] = React.useState(false);
    const [showResizeControls, setShowResizeControls] = React.useState(false);

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
    // Slider reference for mobile resize control
    const sliderRef = React.useRef(null);

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

    // Mobile detection useEffect
    React.useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Update design position state and update slider value if available
    const updateDesignPosition = React.useCallback(() => {
        if (designRef.current) {
            const x = parseFloat(designRef.current.getAttribute("x")) || 0;
            const y = parseFloat(designRef.current.getAttribute("y")) || 0;
            const width = parseFloat(designRef.current.getAttribute("width")) || 0;
            const height = parseFloat(designRef.current.getAttribute("height")) || 0;
            
            setDesignPosition({ x, y, width, height });
            
            // If we have a slider, update its value based on width
            if (sliderRef.current && !isResizing) {
                const sliderValue = (width / SVG_WIDTH) * 100;
                sliderRef.current.value = sliderValue;
            }
        }
    }, [isResizing]);

    // Initialize design position and size
    React.useEffect(() => {
        if (designUrl && svgRef.current) {
            const img = new Image();
            img.onload = () => {
                const aspectRatio = img.height / img.width;
                const initialWidth = SVG_WIDTH * 0.2;
                const initialHeight = initialWidth * aspectRatio;
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

                    designImage.addEventListener('mousedown', handleDragStart);
                    // Use specialized touch handler for mobile
                    designImage.addEventListener('touchstart', handleTouchStart);
                    
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

    // Specialized touch handler for mobile dragging
    const handleTouchStart = React.useCallback((e) => {
        e.preventDefault();
        if (!designRef.current) return;
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            setIsDragging(true);
            const x = parseFloat(designRef.current.getAttribute("x")) || 0;
            const y = parseFloat(designRef.current.getAttribute("y")) || 0;
            startPositionRef.current = { x, y };
            const svgPoint = screenToSVGPoint(touch.clientX, touch.clientY);
            startPosRef.current = svgPoint;
            console.log('Touch drag start:', { position: startPositionRef.current, touch: startPosRef.current });
            if (isMobile) {
                setShowResizeControls(true);
            }
        }
    }, [screenToSVGPoint, isMobile]);

    // Start dragging the design (with mobile functionality)
    const handleDragStart = React.useCallback((e) => {
        e.preventDefault();
        if (!designRef.current) return;
        setIsDragging(true);
        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        startPositionRef.current = { x, y };
        const svgPoint = screenToSVGPoint(e.clientX, e.clientY);
        startPosRef.current = svgPoint;
        console.log('Drag start:', { position: startPositionRef.current, mouse: startPosRef.current });
        if (isMobile) {
            setShowResizeControls(true);
        }
    }, [screenToSVGPoint, isMobile]);

    // Start resizing the design
    const handleResizeStart = React.useCallback((e, handle) => {
        e.preventDefault();
        e.stopPropagation();
        if (!designRef.current) return;
        setIsResizing(true);
        currentHandleRef.current = handle;
        const x = parseFloat(designRef.current.getAttribute("x")) || 0;
        const y = parseFloat(designRef.current.getAttribute("y")) || 0;
        const width = parseFloat(designRef.current.getAttribute("width")) || 0;
        const height = parseFloat(designRef.current.getAttribute("height")) || 0;
        startPositionRef.current = { x, y };
        startSizeRef.current = { width, height };
        const svgPoint = screenToSVGPoint(e.clientX, e.clientY);
        startPosRef.current = svgPoint;
        console.log('Resize start:', { position: startPositionRef.current, size: startSizeRef.current, mouse: startPosRef.current, handle });
    }, [screenToSVGPoint]);

    // Mobile-specific resize function using the slider
    const handleSliderResize = React.useCallback((e) => {
        if (!designRef.current) return;
        const sliderValue = parseFloat(e.target.value);
        const sizePercentage = (sliderValue * 0.45 + 5) / 100;
        const newWidth = SVG_WIDTH * sizePercentage;
        const aspectRatio = parseFloat(designRef.current.getAttribute("height")) / parseFloat(designRef.current.getAttribute("width"));
        const newHeight = newWidth * aspectRatio;
        const currentX = parseFloat(designRef.current.getAttribute("x"));
        const currentY = parseFloat(designRef.current.getAttribute("y"));
        const currentCenterX = currentX + (parseFloat(designRef.current.getAttribute("width")) / 2);
        const currentCenterY = currentY + (parseFloat(designRef.current.getAttribute("height")) / 2);
        const newX = currentCenterX - (newWidth / 2);
        const newY = currentCenterY - (newHeight / 2);
        designRef.current.setAttribute("x", newX);
        designRef.current.setAttribute("y", newY);
        designRef.current.setAttribute("width", newWidth);
        designRef.current.setAttribute("height", newHeight);
        updateDesignPosition();
        checkCenterAlignment(newX, newY, newWidth, newHeight);
    }, [updateDesignPosition]);

    // Check if design is close to center and show guides
    const checkCenterAlignment = React.useCallback((x, y, width, height) => {
        const designCenterX = x + (width / 2);
        const designCenterY = y + (height / 2);
        const canvasCenterX = SVG_WIDTH / 2;
        const canvasCenterY = SVG_HEIGHT / 2;
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

    // Handle mouse/touch move for drag and resize
    const handleMouseMove = React.useCallback((e) => {
        if (!isDragging && !isResizing) return;
        if (!designRef.current) return;
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        const currentPoint = screenToSVGPoint(clientX, clientY);
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
                case 'se':
                    newWidth = startSizeRef.current.width + dx;
                    newHeight = newWidth * aspectRatio;
                    break;
                case 'sw':
                    newWidth = startSizeRef.current.width - dx;
                    newHeight = newWidth * aspectRatio;
                    newX = startPositionRef.current.x + dx;
                    break;
                case 'ne':
                    newWidth = startSizeRef.current.width + dx;
                    newHeight = newWidth * aspectRatio;
                    newY = startPositionRef.current.y + startSizeRef.current.height - newHeight;
                    break;
                case 'nw':
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

    // Create resize handles (desktop only)
    const createResizeHandles = () => {
        if (isMobile) return [];
        const handleSize = 16;
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
            ...createResizeHandles()
        ]) : null;
        return [productImage, ...centerGuides, designGroup].filter(Boolean);
    };

    // Create mobile resize controls (slider and center button)
    const createResizeControls = () => {
        if (!isMobile || !showResizeControls) return null;
        const sliderValue = designPosition.width / SVG_WIDTH * 100;
        return React.createElement('div', {
            style: {
                position: 'absolute',
                bottom: '80px',
                left: '10%',
                width: '80%',
                padding: '15px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                borderRadius: '8px',
                zIndex: 3000,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center'
            }
        }, [
            React.createElement('label', {
                style: {
                    color: 'white',
                    marginBottom: '10px',
                    fontSize: '16px',
                    fontWeight: 'bold'
                }
            }, 'Adjust Size:'),
            React.createElement('div', {
                style: {
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }
            }, [
                React.createElement('svg', {
                    width: '24',
                    height: '24',
                    viewBox: '0 0 24 24',
                    fill: 'white',
                    style: { minWidth: '24px' }
                }, [
                    React.createElement('path', {
                        d: 'M13,10H18V12H13V17H11V12H6V10H11V5H13V10Z',
                        transform: 'scale(0.7) translate(5, 5)'
                    })
                ]),
                React.createElement('input', {
                    ref: sliderRef,
                    type: 'range',
                    min: '0',
                    max: '100',
                    defaultValue: sliderValue,
                    style: {
                        width: '70%',
                        margin: '0 10px',
                        height: '30px'
                    },
                    onChange: handleSliderResize
                }),
                React.createElement('svg', {
                    width: '24',
                    height: '24',
                    viewBox: '0 0 24 24',
                    fill: 'white',
                    style: { minWidth: '24px' }
                }, [
                    React.createElement('path', {
                        d: 'M13,10H18V12H13V17H11V12H6V10H11V5H13V10Z',
                        transform: 'scale(1.3) translate(2, 2)'
                    })
                ])
            ]),
            React.createElement('button', {
                onClick: () => {
                    if (!designRef.current) return;
                    const width = parseFloat(designRef.current.getAttribute("width"));
                    const height = parseFloat(designRef.current.getAttribute("height"));
                    const centerX = SVG_WIDTH / 2 - width / 2;
                    const centerY = SVG_HEIGHT / 2 - height / 2;
                    designRef.current.setAttribute("x", centerX);
                    designRef.current.setAttribute("y", centerY);
                    updateDesignPosition();
                    setShowCenterGuide({ vertical: true, horizontal: true });
                    setTimeout(() => {
                        setShowCenterGuide({ vertical: false, horizontal: false });
                    }, 1000);
                },
                style: {
                    marginTop: '15px',
                    padding: '8px 15px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px'
                }
            }, 'Center Design')
        ]);
    };

    // Update instructions based on device type
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
    }, isMobile ? 'Tap and drag to move design' : 'Drag to move, drag corners to resize');

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

    // Define svgContainer first
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

    // Then define your buttons
    const toggleButton = React.createElement('button', {
        onClick: () => {
            console.log('Toggle clicked, switching from', showBackImage ? 'back' : 'front', 'to', showBackImage ? 'front' : 'back');
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

    // Finally, use them all in the container
    const container = React.createElement('div', {
        style: {
            position: 'relative',
            width: '100%',
            height: '100%',
            overflow: 'hidden'
        }
    }, [
        svgContainer,
        saveButton,
        toggleButton,
        instructions,
        closeButton,
        createResizeControls()
    ].filter(Boolean));

    return React.StrictMode ?
        React.createElement(React.StrictMode, null, container) :
        container;
};

// Make available globally
window.DesignPlacer = DesignPlacer;