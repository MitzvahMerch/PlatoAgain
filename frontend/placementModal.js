// placementModal.js
const createPlacementModal = () => {
    const modal = document.createElement('div');
    modal.className = 'placement-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: none;
        z-index: 1000;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'placement-modal-content';
    modalContent.style.cssText = `
        position: relative;
        width: 90%;
        height: 90%;
        margin: 2% auto;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        z-index: 2000;
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Track if the modal was closed due to save or cancel
    let wasCancelled = false;
    let onHideCallback = null;
    
    // Create the modal interface with improved methods
    const modalInterface = {
        modal,
        content: modalContent,
        onHide: null, // Custom callback that can be set by other components
        
        show: () => {
            modal.style.display = 'block';
            wasCancelled = true; // Assume cancel until proven otherwise (save called)
        },
        
        hide: () => {
            modal.style.display = 'none';
            
            // If this was a cancellation and not a save operation
            if (wasCancelled) {
                console.log('Design placement was cancelled');
                
                // Reset the upload status
                const fileInput = document.getElementById('image-upload');
                if (fileInput) fileInput.value = '';
                
                // Reset the upload button appearance
                const uploadButton = document.querySelector('.chat-upload-button svg');
                if (uploadButton) {
                    uploadButton.innerHTML = `
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    `;
                    uploadButton.style.color = 'var(--secondary-color)';
                }
            }
            
            // Call any custom onHide callback that was set
            if (typeof modalInterface.onHide === 'function') {
                modalInterface.onHide();
            }
        },
        
        // Method to be called when save is successful
        confirmSave: () => {
            wasCancelled = false; // This was not a cancellation
        }
    };
    
    return modalInterface;
};

// Initialize and export the modal
window.placementModal = createPlacementModal();