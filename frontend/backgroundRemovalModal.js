// backgroundRemovalModal.js - Provides options for image background handling with Clipping Magic API

// Helper function to load an image from URL
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

const createBackgroundRemovalModal = () => {
    // Create the modal container
    const modal = document.createElement('div');
    modal.className = 'background-removal-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: none;
        z-index: 2000;
        align-items: center;
        justify-content: center;
    `;
    
    // Create modal content container
    const modalContent = document.createElement('div');
    modalContent.className = 'background-removal-modal-content';
    modalContent.style.cssText = `
        width: 600px;
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        position: relative;
    `;
    
    // Add close button (X)
    const closeButton = document.createElement('div');
    closeButton.className = 'background-removal-close-button';
    closeButton.innerHTML = '&times;'; // X symbol
    closeButton.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 24px;
        font-weight: bold;
        color: #555;
        cursor: pointer;
        z-index: 2100;
    `;

    // Add click event to close the modal
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
        // Clean up URLs to prevent memory leaks
        if (processedOptions) {
            URL.revokeObjectURL(processedOptions.original.url);
            URL.revokeObjectURL(processedOptions.bgRemove.url);
            processedOptions = null;
        }
        currentFile = null;
    });
    
    // Create modal title
    const modalTitle = document.createElement('h3');
    modalTitle.textContent = 'Choose Background Option';
    modalTitle.style.cssText = `
        margin-top: 0;
        margin-bottom: 20px;
        font-size: 20px;
        color: #333;
        text-align: center;
    `;
    
    // Create options container
    const optionsContainer = document.createElement('div');
    optionsContainer.style.cssText = `
        display: flex;
        justify-content: space-around;
        gap: 20px;
    `;
    
    // Add loading indicator overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'background-removal-loading-overlay';
    loadingOverlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 10;
        border-radius: 8px;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    const loadingText = document.createElement('div');
    loadingText.textContent = 'Processing image options...';
    loadingText.style.cssText = `
        margin-top: 16px;
        font-size: 16px;
    `;
    
    loadingOverlay.appendChild(spinner);
    loadingOverlay.appendChild(loadingText);
    modalContent.appendChild(loadingOverlay);
    loadingOverlay.style.display = 'none';
    
    // Helper function to create option cards
    const createOptionCard = (title, imgSrc) => {
        const card = document.createElement('div');
        card.className = 'background-option-card';
        card.style.cssText = `
            flex: 1;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            transition: border-color 0.2s, transform 0.2s;
            text-align: center;
            max-width: 250px;
        `;
        
        // Hover effect
        card.addEventListener('mouseover', () => {
            card.style.borderColor = '#0066ff';
            card.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseout', () => {
            card.style.borderColor = '#e0e0e0';
            card.style.transform = 'translateY(0)';
        });
        
        // Create image container (maintain aspect ratio)
        const imgContainer = document.createElement('div');
        imgContainer.style.cssText = `
            padding-bottom: 100%;
            position: relative;
            background: #f5f5f5;
        `;
        
        // Create image (absolutely positioned within container)
        const img = document.createElement('img');
        img.src = imgSrc || '';
        img.alt = title;
        img.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
            padding: 10px;
            box-sizing: border-box;
        `;
        
        imgContainer.appendChild(img);
        
        // Create title
        const titleDiv = document.createElement('div');
        titleDiv.textContent = title;
        titleDiv.style.cssText = `
            padding: 12px;
            font-weight: 500;
            border-top: 1px solid #e0e0e0;
            background: #f9f9f9;
        `;
        
        card.appendChild(imgContainer);
        card.appendChild(titleDiv);
        
        return { card, img };
    };
    
    // Create the option cards with placeholder images
    const { card: option1Card, img: option1Img } = createOptionCard('Keep Original', '');
    const { card: option2Card, img: option2Img } = createOptionCard('Remove Background', '');
    
    optionsContainer.appendChild(option1Card);
    optionsContainer.appendChild(option2Card);
    
    // Add all elements to the modal
    modalContent.appendChild(closeButton);
    modalContent.appendChild(modalTitle);
    modalContent.appendChild(optionsContainer);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Function to process image with Clipping Magic API
    const processWithBackgroundRemoval = async (file) => {
        try {
            // Explicitly hardcode the base URL to ensure it's correct
            const API_ENDPOINT = 'https://platosprints-5w8mn.ondigitalocean.app/api/remove-background';
            
            console.log('Calling background removal API at:', API_ENDPOINT);
            
            // Create FormData with the file
            const formData = new FormData();
            formData.append('image', file);
            
            // Call the API with detailed error logging
            console.log('Sending background removal request with file:', file.name, 'size:', file.size);
            
            // Call the API (via our backend proxy)
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData
            });
            
            console.log('Background removal API response status:', response.status, response.statusText);
            
            if (!response.ok) {
                // If response is not ok, try to get more details from the response
                let errorDetails = '';
                try {
                    const errorJson = await response.json();
                    errorDetails = JSON.stringify(errorJson);
                } catch (e) {
                    try {
                        errorDetails = await response.text();
                    } catch (e2) {
                        errorDetails = 'No additional error details available';
                    }
                }
                
                console.error('Background removal API error details:', errorDetails);
                throw new Error(`Failed to remove background: ${response.statusText}. Details: ${errorDetails}`);
            }
            
            // Get the processed image blob
            const blob = await response.blob();
            console.log('Successfully received processed image, size:', blob.size);
            
            // Create URL and File objects for the result
            const processedUrl = URL.createObjectURL(blob);
            const processedFile = new File([blob], file.name, { type: 'image/png' });
            
            return { success: true, url: processedUrl, processedFile };
        } catch (error) {
            console.error('Error calling background removal API:', error);
            
            // Check if server is running
            try {
                const healthCheck = await fetch('https://platosprints-5w8mn.ondigitalocean.app/api/health');
                console.log('Server health check:', healthCheck.status, await healthCheck.text());
            } catch (healthError) {
                console.error('Server health check failed - server may be down:', healthError);
            }
            
            // Fallback to client-side processing if API fails
            console.log('Falling back to client-side processing...');
            return processImageClientSide(file);
        }
    };
    
    // Client-side fallback for processing (in case API fails)
    const processImageClientSide = async (file) => {
        try {
            console.log('Starting client-side image processing fallback');
            const imageUrl = URL.createObjectURL(file);
            
            // Load the image into a canvas for processing
            const img = await loadImage(imageUrl);
            console.log('Image loaded for client-side processing, dimensions:', img.width, 'x', img.height);
            
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            // Get image data for pixel manipulation
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Remove white background with a simple threshold approach
            const threshold = 240; // RGB threshold for what's considered "white"
            
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                
                // If pixel is white-ish, make it transparent
                if (r > threshold && g > threshold && b > threshold) {
                    data[i + 3] = 0; // Set alpha to 0 (transparent)
                }
            }
            
            // Put the modified image data back on the canvas
            ctx.putImageData(imageData, 0, 0);
            
            // Convert canvas to blob and URL
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
            console.log('Client-side processing complete, result size:', blob.size);
            
            const processedUrl = URL.createObjectURL(blob);
            
            // Create a new File object
            const processedFile = new File([blob], file.name, { type: 'image/png' });
            
            return { success: true, url: processedUrl, processedFile };
        } catch (error) {
            console.error('Error in client-side processing fallback:', error);
            return { 
                success: false, 
                error: error.message,
                url: URL.createObjectURL(file),
                processedFile: file
            };
        }
    };

    // Process all image options at once
    const prepareAllOptions = async (file) => {
        try {
            // Create URL for the original image
            const originalUrl = URL.createObjectURL(file);
            
            // Process the image with background removal API
            const bgRemoveResult = await processWithBackgroundRemoval(file);
            
            // Return all results
            return {
                success: true,
                original: { 
                    success: true, 
                    url: originalUrl, 
                    processedFile: file 
                },
                bgRemove: bgRemoveResult
            };
        } catch (error) {
            console.error('Error preparing image options:', error);
            return { 
                success: false, 
                error: error.message,
                original: { 
                    success: true, 
                    url: URL.createObjectURL(file), 
                    processedFile: file 
                }
            };
        }
    };
    
    // Store processed options and the original file
    let processedOptions = null;
    let currentFile = null;
    
    // Return the modal interface
    return {
        modal,
        content: modalContent,
        show: async (imageUrl, file, callback) => {
            currentFile = file;
            
            // Show loading overlay
            loadingOverlay.style.display = 'flex';
            modal.style.display = 'flex';
            
            try {
                // Process both versions of the image
                processedOptions = await prepareAllOptions(file);
                
                if (!processedOptions.success) {
                    throw new Error(processedOptions.error || 'Failed to process image options');
                }
                
                // Update the images in the cards
                option1Img.src = processedOptions.original.url;
                option2Img.src = processedOptions.bgRemove.url;
                
                // Hide loading overlay
                loadingOverlay.style.display = 'none';
                
                // Set click handlers for each option
                option1Card.onclick = () => {
                    modal.style.display = 'none';
                    callback(processedOptions.original);
                };
                
                option2Card.onclick = () => {
                    modal.style.display = 'none';
                    callback(processedOptions.bgRemove);
                };
                
            } catch (error) {
                console.error('Error showing background removal options:', error);
                // Hide loading and close modal
                loadingOverlay.style.display = 'none';
                modal.style.display = 'none';
                // Call callback with original image as fallback
                callback({ 
                    success: true, 
                    url: URL.createObjectURL(file), 
                    processedFile: file,
                    error: error.message
                });
            }
        },
        hide: () => {
            modal.style.display = 'none';
            loadingOverlay.style.display = 'none';
            
            // Clean up URLs to prevent memory leaks
            if (processedOptions) {
                URL.revokeObjectURL(processedOptions.original.url);
                URL.revokeObjectURL(processedOptions.bgRemove.url);
                processedOptions = null;
            }
            
            currentFile = null;
        }
    };
};

// Initialize and export the modal
window.backgroundRemovalModal = createBackgroundRemovalModal();