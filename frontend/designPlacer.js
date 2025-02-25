const DesignPlacer = ({ frontImage, backImage, designUrl, onSave }) => {
    console.log('DesignPlacer props:', { frontImage, backImage, designUrl });
    
    const [showBackImage, setShowBackImage] = React.useState(false);
    const [position, setPosition] = React.useState({ x: 400, y: 300 });
    const [scale, setScale] = React.useState(1);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isResizing, setIsResizing] = React.useState(false);
    const [designSize, setDesignSize] = React.useState({ width: 0, height: 0 });
    const [productDimensions, setProductDimensions] = React.useState({ width: 0, height: 0 });
    const containerRef = React.useRef(null);
    const designRef = React.useRef(null);
    const startPosRef = React.useRef({ x: 0, y: 0 });
    const startScaleRef = React.useRef(1);

    React.useEffect(() => {
        const img = new Image();
        img.onload = () => {
            setProductDimensions({
                width: img.width,
                height: img.height
            });
        };
        img.src = showBackImage ? backImage : frontImage;
    }, [showBackImage, frontImage, backImage]);


    React.useEffect(() => {
        console.log('Loading design image effect triggered');
        const img = new Image();
        img.onload = () => {
            console.log('Design image loaded with dimensions:', { width: img.width, height: img.height });
            setDesignSize({ width: img.width, height: img.height });
            
            const container = containerRef.current;
            if (container) {
                const maxScale = Math.min(
                    (container.clientWidth * 0.3) / img.width,
                    (container.clientHeight * 0.3) / img.height
                );
                console.log('Setting initial scale:', maxScale);
                setScale(maxScale);
            }
        };
        img.src = designUrl;
    }, [designUrl]);

    const handleMouseDown = (e, type) => {
        console.log('Mouse down event:', { type, clientX: e.clientX, clientY: e.clientY });
        e.stopPropagation(); // Prevent event bubbling
        
        if (type === 'drag') {
            console.log('Starting drag operation');
            setIsDragging(true);
            const startPos = {
                x: e.clientX - position.x,
                y: e.clientY - position.y
            };
            console.log('Drag start position:', startPos);
            startPosRef.current = startPos;
        } else if (type === 'resize') {
            console.log('Starting resize operation');
            setIsResizing(true);
            const startPos = {
                x: e.clientX,
                y: e.clientY
            };
            console.log('Resize start position:', startPos);
            startPosRef.current = startPos;
            startScaleRef.current = scale;
            console.log('Current scale at resize start:', scale);
        }
    };

    const handleMouseMove = (e) => {
        if (isDragging) {
            const newX = e.clientX - startPosRef.current.x;
            const newY = e.clientY - startPosRef.current.y;
            console.log('Dragging to position:', { newX, newY });
            setPosition({ x: newX, y: newY });
        } else if (isResizing) {
            console.log('Resize move event:', { clientX: e.clientX, clientY: e.clientY });
            const dx = e.clientX - startPosRef.current.x;
            const dy = e.clientY - startPosRef.current.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const direction = dx + dy > 0 ? 1 : -1;
            
            console.log('Resize calculations:', {
                dx,
                dy,
                distance,
                direction,
                startScale: startScaleRef.current
            });
            
            const newScale = startScaleRef.current * (1 + direction * distance * 0.005);
            const clampedScale = Math.max(0.01, Math.min(2, newScale));
            console.log('New scale:', { raw: newScale, clamped: clampedScale });
            setScale(clampedScale);
        }
    };

    const handleMouseUp = () => {
        if (isDragging) {
            console.log('Ending drag operation');
            setIsDragging(false);
        }
        if (isResizing) {
            console.log('Ending resize operation');
            setIsResizing(false);
        }
    };

    React.useEffect(() => {
        console.log('Setting up mouse event listeners');
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            console.log('Cleaning up mouse event listeners');
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, isResizing]);

    // Modify the handleSave function in DesignPlacer.js
    const handleSave = () => {
        // Get HTML elements
        const productImg = containerRef.current.querySelector('img[alt="Product"]');
        const designElement = designRef.current;
        
        if (!productImg || !designElement) {
            console.error('Required elements not found');
            return;
        }
    
        // Pass the actual element references to the onSave callback
        onSave?.({
            designElement: designElement,
            productImg: productImg,
            showBackImage: showBackImage,
            designUrl: designUrl // Pass the URL for loading the original image
        });
    };

    const scaledWidth = designSize.width * scale;
    const scaledHeight = designSize.height * scale;
    console.log('Calculated scaled dimensions:', { scaledWidth, scaledHeight });

    // Create the resize handles with higher z-index
    const resizeHandles = ['nw', 'ne', 'se', 'sw'].map(corner => 
        React.createElement('div', {
            key: corner,
            style: {
                position: 'absolute',
                width: '16px',
                height: '16px',
                backgroundColor: 'white',
                border: '2px solid #666',
                borderRadius: '50%',
                cursor: 'pointer',
                zIndex: 2000,
                ...(corner === 'nw' ? { top: -8, left: -8 } :
                   corner === 'ne' ? { top: -8, right: -8 } :
                   corner === 'se' ? { bottom: -8, right: -8 } :
                   { bottom: -8, left: -8 })
            },
            onMouseDown: (e) => {
                console.log('Resize handle clicked:', corner);
                handleMouseDown(e, 'resize');
            }
        })
    );

    // Design layer with image and resize handles
    const designLayer = React.createElement('div', {
        ref: designRef,
        style: {
            position: 'absolute',
            left: position.x - (scaledWidth / 2),
            top: position.y - (scaledHeight / 2),
            width: scaledWidth,
            height: scaledHeight,
            cursor: isDragging ? 'grabbing' : 'grab',
            zIndex: 1000,
            userSelect: 'none',
            touchAction: 'none'
        },
        onMouseDown: (e) => handleMouseDown(e, 'drag')
    }, [
        React.createElement('img', {
            key: 'design-image',
            src: designUrl,
            alt: "Design",
            style: {
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                pointerEvents: 'none'
            }
        }),
        ...resizeHandles
    ]);

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

    // Main container
    const container = React.createElement('div', {
        ref: containerRef,
        style: {
            position: 'relative',
            width: '100%',
            height: '600px',
            backgroundColor: '#f0f0f0',
            overflow: 'hidden'
        }
    }, [
        // Product image background
        React.createElement('img', {
            key: 'product-image',
            src: showBackImage ? backImage : frontImage,
            alt: "Product",
            style: {
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                pointerEvents: 'none'
            }
        }),
        designLayer,
        saveButton,
        toggleButton
    ]);

    return React.StrictMode ? 
        React.createElement(React.StrictMode, null, container) : 
        container;
};

// Make available globally
window.DesignPlacer = DesignPlacer;