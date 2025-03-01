// shippingModal.js
const createShippingModal = () => {
    const modal = document.createElement('div');
    modal.className = 'shipping-modal';
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
    modalContent.className = 'shipping-modal-content';
    modalContent.style.cssText = `
        position: relative;
        width: 90%;
        max-width: 500px;
        margin: 5% auto;
        background: white;
        border-radius: 8px;
        padding: 20px;
        color: black;
        z-index: 2000;
    `;
    
    // Header
    const modalHeader = document.createElement('div');
    modalHeader.className = 'shipping-modal-header';
    modalHeader.innerHTML = '<h2>Complete Your Order</h2>';
    modalHeader.style.cssText = `
        margin-bottom: 20px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
        text-align: center;
        color: var(--primary-color);
    `;
    
    // Order summary
    const orderSummary = document.createElement('div');
    orderSummary.className = 'order-summary';
    orderSummary.innerHTML = `
        <h3>Order Summary</h3>
        <p id="modal-product-name"></p>
        <p id="modal-quantity"></p>
        <p id="modal-total"></p>
    `;
    orderSummary.style.cssText = `
        margin-bottom: 20px;
        padding: 15px;
        background: #f9f9f9;
        border-radius: 4px;
    `;
    
    // Form
    const form = document.createElement('form');
    form.className = 'shipping-form';
    form.innerHTML = `
        <div class="form-group">
            <label for="customer-name">Full Name</label>
            <input type="text" id="customer-name" placeholder="Your full name" required>
        </div>
        
        <div class="form-group">
            <label for="customer-address">Shipping Address</label>
            <input type="text" id="customer-address" placeholder="Enter your shipping address" required>
            <div id="address-suggestions" class="address-suggestions"></div>
        </div>
        
        <div class="form-group">
            <label for="customer-email">Email for Invoice</label>
            <input type="email" id="customer-email" placeholder="Your email address" required>
        </div>
    `;
    form.style.cssText = `
        margin-bottom: 20px;
    `;
    
    // Add form styling
    const style = document.createElement('style');
    style.textContent = `
        .shipping-form .form-group {
            margin-bottom: 15px;
            position: relative;
        }
        
        .shipping-form label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .shipping-form input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .shipping-form input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .address-suggestions {
            position: absolute;
            width: 100%;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 4px 4px;
            z-index: 2050;
            max-height: 200px;
            overflow-y: auto;
            display: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .suggestion-item {
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .suggestion-item:last-child {
            border-bottom: none;
        }
        
        .suggestion-item:hover {
            background-color: #f5f5f5;
        }
    `;
    document.head.appendChild(style);
    
    // Buttons
    const modalFooter = document.createElement('div');
    modalFooter.className = 'modal-footer';
    modalFooter.innerHTML = `
        <button id="complete-order-btn" type="submit">Complete Order</button>
        <button id="cancel-order-btn" type="button">Cancel</button>
    `;
    modalFooter.style.cssText = `
        display: flex;
        justify-content: space-between;
    `;
    
    const completeOrderBtn = modalFooter.querySelector('#complete-order-btn');
    completeOrderBtn.style.cssText = `
        padding: 10px 20px;
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        flex: 1;
        margin-right: 10px;
    `;
    
    const cancelOrderBtn = modalFooter.querySelector('#cancel-order-btn');
    cancelOrderBtn.style.cssText = `
        padding: 10px 20px;
        background-color: #f0f0f0;
        color: #333;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    `;
    
    // Assembly
    form.appendChild(modalFooter);
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(orderSummary);
    modalContent.appendChild(form);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event handlers
    cancelOrderBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Close when clicking outside modal content
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // This object will be returned from the function
    const modalObj = {
        modal,
        form,
        show: (orderDetails) => {
            if (orderDetails) {
                document.getElementById('modal-product-name').textContent = orderDetails.product || '';
                document.getElementById('modal-quantity').textContent = orderDetails.quantity || '';
                document.getElementById('modal-total').textContent = `Total: $${orderDetails.total || '0.00'}`;
            }
            modal.style.display = 'block';
            
            // Initialize address autocomplete with Places API v1
            setTimeout(() => {
                const addressInput = document.getElementById('customer-address');
                const suggestionsContainer = document.getElementById('address-suggestions');
                
                // Function to fetch autocomplete suggestions
                let debounceTimer;
                addressInput.addEventListener('input', function() {
                    clearTimeout(debounceTimer);
                    
                    if (this.value.length < 3) {
                        suggestionsContainer.style.display = 'none';
                        return;
                    }
                    
                    debounceTimer = setTimeout(() => {
                        fetch('https://places.googleapis.com/v1/places:autocomplete', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Goog-Api-Key': 'AIzaSyAmKiH2TBznHxqzk7B9OA8hnKThsm7FE74',
                                'X-Goog-FieldMask': '*'
                            },
                            body: JSON.stringify({
                                'input': this.value
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            suggestionsContainer.innerHTML = '';
                            
                            if (data.suggestions && data.suggestions.length > 0) {
                                suggestionsContainer.style.display = 'block';
                                
                                data.suggestions.forEach(suggestion => {
                                    const div = document.createElement('div');
                                    div.className = 'suggestion-item';
                                    div.textContent = suggestion.placePrediction.text.text;
                                    
                                    div.addEventListener('click', function() {
                                        addressInput.value = suggestion.placePrediction.text.text;
                                        suggestionsContainer.style.display = 'none';
                                    });
                                    
                                    suggestionsContainer.appendChild(div);
                                });
                            } else {
                                suggestionsContainer.style.display = 'none';
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching autocomplete suggestions:', error);
                            suggestionsContainer.style.display = 'none';
                        });
                    }, 300); // Debounce time in milliseconds
                });
                
                // Close suggestions when clicking outside
                document.addEventListener('click', function(e) {
                    if (!e.target.closest('#customer-address') && !e.target.closest('#address-suggestions')) {
                        suggestionsContainer.style.display = 'none';
                    }
                });
                
                // Allow keyboard navigation through suggestions
                addressInput.addEventListener('keydown', function(e) {
                    const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');
                    
                    if (suggestions.length === 0 || suggestionsContainer.style.display === 'none') {
                        return;
                    }
                    
                    // Find currently focused suggestion
                    const focused = suggestionsContainer.querySelector('.suggestion-item.focused');
                    const focusedIndex = focused ? Array.from(suggestions).indexOf(focused) : -1;
                    
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        if (focused) {
                            focused.classList.remove('focused');
                            const nextIndex = (focusedIndex + 1) % suggestions.length;
                            suggestions[nextIndex].classList.add('focused');
                            suggestions[nextIndex].scrollIntoView({ block: 'nearest' });
                        } else {
                            suggestions[0].classList.add('focused');
                            suggestions[0].scrollIntoView({ block: 'nearest' });
                        }
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        if (focused) {
                            focused.classList.remove('focused');
                            const prevIndex = (focusedIndex - 1 + suggestions.length) % suggestions.length;
                            suggestions[prevIndex].classList.add('focused');
                            suggestions[prevIndex].scrollIntoView({ block: 'nearest' });
                        } else {
                            const lastIndex = suggestions.length - 1;
                            suggestions[lastIndex].classList.add('focused');
                            suggestions[lastIndex].scrollIntoView({ block: 'nearest' });
                        }
                    } else if (e.key === 'Enter' && focused) {
                        e.preventDefault();
                        addressInput.value = focused.textContent;
                        suggestionsContainer.style.display = 'none';
                    } else if (e.key === 'Escape') {
                        suggestionsContainer.style.display = 'none';
                    }
                });
            }, 100);
        },
        hide: () => {
            modal.style.display = 'none';
        },
        getFormData: () => {
            return {
                name: document.getElementById('customer-name').value,
                address: document.getElementById('customer-address').value,
                email: document.getElementById('customer-email').value
            };
        }
    };
    
    return modalObj;
};

// Initialize and export the modal
window.shippingModal = createShippingModal();