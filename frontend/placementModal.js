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
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    return {
        modal,
        content: modalContent,
        show: () => modal.style.display = 'block',
        hide: () => modal.style.display = 'none'
    };
};

// Initialize and export the modal
window.placementModal = createPlacementModal();