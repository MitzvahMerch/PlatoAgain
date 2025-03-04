// shippingModal.js
const createShippingModal = () => {
    console.log('Initializing shipping modal...');
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

        <div class="form-group">
            <label for="received-by-date">Receive By Date</label>
            <input type="text" id="received-by-date" placeholder="Select a date" readonly required>
            <div id="date-picker-container" class="date-picker-container"></div>
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
        
        .shipping-form input[readonly] {
            background-color: #f9f9f9;
            cursor: pointer;
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

        /* Date Picker Styles */
        .date-picker-container {
            position: absolute;
            width: 320px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            z-index: 2050;
            display: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 10px;
        }
        
        .date-picker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .date-picker-month {
            font-weight: bold;
            text-align: center;
            flex-grow: 1;
        }
        
        .date-picker-nav {
            cursor: pointer;
            padding: 5px 10px;
            background: #f5f5f5;
            border: none;
            border-radius: 4px;
        }
        
        .date-picker-nav:hover {
            background: #e0e0e0;
        }
        
        .date-picker-weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            margin-bottom: 5px;
        }
        
        .date-picker-weekday {
            text-align: center;
            font-weight: bold;
            font-size: 12px;
            color: #666;
        }
        
        .date-picker-days {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
        }
        
        .date-picker-day {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 35px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .date-picker-day:hover {
            background-color: #f0f0f0;
        }
        
        .date-picker-day.active {
            background-color: var(--primary-color);
            color: white;
        }
        
        .date-picker-day.disabled {
            color: #ccc;
            cursor: not-allowed;
        }
        
        .date-picker-day.other-month {
            color: #aaa;
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

    // Create and setup date picker
    const setupDatePicker = () => {
        console.log('Setting up date picker...');
        const dateInput = document.getElementById('received-by-date');
        const datePickerContainer = document.getElementById('date-picker-container');
        
        if (!dateInput) {
            console.error('Date input element not found!');
            return;
        }
        
        if (!datePickerContainer) {
            console.error('Date picker container element not found!');
            return;
        }

        console.log('Date picker elements found, initializing...');

        // Create date picker elements
        datePickerContainer.innerHTML = `
    <div class="date-picker-header">
        <button type="button" class="date-picker-nav prev">&lt;</button>
        <div class="date-picker-month">Month Year</div>
        <button type="button" class="date-picker-nav next">&gt;</button>
    </div>
    <div class="date-picker-weekdays">
        <div class="date-picker-weekday">Sun</div>
        <div class="date-picker-weekday">Mon</div>
        <div class="date-picker-weekday">Tue</div>
        <div class="date-picker-weekday">Wed</div>
        <div class="date-picker-weekday">Thu</div>
        <div class="date-picker-weekday">Fri</div>
        <div class="date-picker-weekday">Sat</div>
    </div>
    <div class="date-picker-days"></div>
`;

        // Initialize variables
        let currentDate = new Date();
        let selectedDate = null;
        
        // Function to format date as MM/DD/YYYY
        const formatDate = (date) => {
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const year = date.getFullYear();
            return `${month}/${day}/${year}`;
        };
        
        // Function to render calendar
        // Function to render calendar
const renderCalendar = () => {
    console.log('Rendering calendar...');
    const daysContainer = datePickerContainer.querySelector('.date-picker-days');
    const monthDisplay = datePickerContainer.querySelector('.date-picker-month');
    
    if (!daysContainer) {
        console.error('Days container element not found in date picker!');
        return;
    }
    
    if (!monthDisplay) {
        console.error('Month display element not found in date picker!');
        return;
    }
    
    // Format month display
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
    monthDisplay.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
    
    // Get first day of month and last day of month
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    
    // Get day of week for first day (0 = Sunday, 6 = Saturday)
    const firstDayOfWeek = firstDay.getDay();
    
    // Get total days in month
    const totalDays = lastDay.getDate();
    
    // Clear container
    daysContainer.innerHTML = '';
    
    // Get today's date for comparison
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Calculate minimum shipping date (today + 10 days)
    const minShippingDate = new Date(today);
    minShippingDate.setDate(today.getDate() + 10);
    
    // Calculate standard free shipping date (today + 17 days)
    const freeShippingDate = new Date(today);
    freeShippingDate.setDate(today.getDate() + 17);
    
    // Add days from previous month to fill first row
    const prevMonthLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();
    for (let i = 0; i < firstDayOfWeek; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'date-picker-day other-month';
        dayDiv.textContent = prevMonthLastDay - firstDayOfWeek + i + 1;
        daysContainer.appendChild(dayDiv);
    }
    
    // Add days for current month
    for (let i = 1; i <= totalDays; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'date-picker-day';
        dayDiv.textContent = i;
        
        // Check if day is before minimum shipping date
        const dayDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), i);
        
        if (dayDate < today || dayDate < minShippingDate) {
            dayDiv.className += ' disabled';
            dayDiv.title = 'Delivery not available for this date';
        } else {
            // Check if this is the free shipping date
            const dayTime = dayDate.getTime();
            const freeShippingTime = freeShippingDate.getTime();
            
            // Use a date comparison that checks for the same day
            const isSameDay = 
                dayDate.getDate() === freeShippingDate.getDate() && 
                dayDate.getMonth() === freeShippingDate.getMonth() &&
                dayDate.getFullYear() === freeShippingDate.getFullYear();
            
            if (isSameDay) {
                dayDiv.style.border = '2px solid green';
                dayDiv.style.backgroundColor = '#e6f7e6';
                dayDiv.title = 'Free standard shipping!';
            }
            
            // Check if this is the selected date
            if (selectedDate && 
                selectedDate.getDate() === i && 
                selectedDate.getMonth() === currentDate.getMonth() && 
                selectedDate.getFullYear() === currentDate.getFullYear()) {
                dayDiv.className += ' active';
            }
            
            // Add click event to selectable days
            dayDiv.addEventListener('click', () => {
                console.log(`Day ${i} clicked`);
                // Update selected date
                selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), i);
                
                // Update input value
                dateInput.value = formatDate(selectedDate);
                console.log(`Date input updated to: ${dateInput.value}`);
                
                // Hide date picker
                datePickerContainer.style.display = 'none';
                
                // Re-render to update active state
                renderCalendar();
            });
        }
        
        daysContainer.appendChild(dayDiv);
    }
    
    // Fill remaining cells with next month's days
    const totalCellsUsed = firstDayOfWeek + totalDays;
    const cellsToFill = Math.ceil(totalCellsUsed / 7) * 7 - totalCellsUsed;
    
    for (let i = 1; i <= cellsToFill; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'date-picker-day other-month';
        dayDiv.textContent = i;
        daysContainer.appendChild(dayDiv);
    }
    
    console.log('Calendar rendering complete');
};
        
        // Navigate to previous month
const prevMonthBtn = datePickerContainer.querySelector('.date-picker-nav.prev');
if (prevMonthBtn) {
    prevMonthBtn.addEventListener('click', (e) => {
        console.log('Previous month button clicked');
        e.stopPropagation(); // Prevent event from reaching document
        e.preventDefault(); // Prevent form submission
        currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1);
        renderCalendar();
    });
} else {
    console.error('Previous month button not found!');
}

// Navigate to next month
const nextMonthBtn = datePickerContainer.querySelector('.date-picker-nav.next');
if (nextMonthBtn) {
    nextMonthBtn.addEventListener('click', (e) => {
        console.log('Next month button clicked');
        e.stopPropagation(); // Prevent event from reaching document
        e.preventDefault(); // Prevent form submission
        currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
        renderCalendar();
    });
} else {
    console.error('Next month button not found!');
}
        
        // Show/hide date picker when clicking on the input
dateInput.addEventListener('click', (e) => {
    console.log('Date input clicked');
    e.stopPropagation(); // Prevent click from propagating to document
    
    const currentDisplay = window.getComputedStyle(datePickerContainer).display;
    console.log(`Current date picker display: ${currentDisplay}`);
    
    if (currentDisplay === 'block') {
        console.log('Hiding date picker');
        datePickerContainer.style.display = 'none';
    } else {
        console.log('Showing date picker');
        
        // Make the date picker highly visible and centered in the modal
        datePickerContainer.style.position = 'absolute';
        datePickerContainer.style.top = '50%';
        datePickerContainer.style.left = '50%';
        datePickerContainer.style.transform = 'translate(-50%, -50%)';
        datePickerContainer.style.zIndex = '9999';
        datePickerContainer.style.backgroundColor = 'white';
        datePickerContainer.style.border = '2px solid var(--primary-color)';
        datePickerContainer.style.display = 'block';
        
        // If no date is selected, set to current date
        if (!selectedDate) {
            const today = new Date();
            currentDate = new Date(today.getFullYear(), today.getMonth(), 1);
        }
        
        renderCalendar();
    }
});
        
        // Close date picker when clicking outside
        document.addEventListener('click', (e) => {
            if (datePickerContainer.style.display === 'block') {
                if (!e.target.closest('#received-by-date') && !e.target.closest('#date-picker-container')) {
                    console.log('Clicked outside date picker, hiding it');
                    datePickerContainer.style.display = 'none';
                }
            }
        });
        
        // Initial render
        console.log('Performing initial calendar render');
        renderCalendar();
    };
    
    // This object will be returned from the function
    const modalObj = {
        modal,
        form,
        show: (orderDetails) => {
            console.log('Showing shipping modal with order details:', orderDetails);
            if (orderDetails) {
                document.getElementById('modal-product-name').textContent = orderDetails.product || '';
                document.getElementById('modal-quantity').textContent = orderDetails.quantity || '';
                document.getElementById('modal-total').textContent = `Total: $${orderDetails.total || '0.00'}`;
            }
            modal.style.display = 'block';
            
            // Initialize address autocomplete and date picker with slight delay to ensure DOM is ready
            console.log('Setting up modal components with delay...');
            setTimeout(() => {
                console.log('Initializing modal components...');
                const addressInput = document.getElementById('customer-address');
                const suggestionsContainer = document.getElementById('address-suggestions');
                
                if (!addressInput) {
                    console.error('Address input element not found!');
                } else if (!suggestionsContainer) {
                    console.error('Address suggestions container not found!');
                } else {
                    console.log('Setting up address autocomplete...');
                    // Function to fetch autocomplete suggestions
                    let debounceTimer;
                    addressInput.addEventListener('input', function() {
                        clearTimeout(debounceTimer);
                        
                        if (this.value.length < 3) {
                            suggestionsContainer.style.display = 'none';
                            return;
                        }
                        
                        debounceTimer = setTimeout(() => {
                            console.log(`Fetching address suggestions for: ${this.value}`);
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
                                    console.log(`Received ${data.suggestions.length} address suggestions`);
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
                                    console.log('No address suggestions received');
                                    suggestionsContainer.style.display = 'none';
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching autocomplete suggestions:', error);
                                suggestionsContainer.style.display = 'none';
                            });
                        }, 300); // Debounce time in milliseconds
                    });
                }
                
                // Close suggestions when clicking outside
                document.addEventListener('click', function(e) {
                    if (suggestionsContainer && suggestionsContainer.style.display === 'block') {
                        if (!e.target.closest('#customer-address') && !e.target.closest('#address-suggestions')) {
                            suggestionsContainer.style.display = 'none';
                        }
                    }
                });
                
                // Allow keyboard navigation through suggestions
                if (addressInput) {
                    addressInput.addEventListener('keydown', function(e) {
                        if (!suggestionsContainer || suggestionsContainer.style.display !== 'block') {
                            return;
                        }
                        
                        const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');
                        if (suggestions.length === 0) {
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
                }

                // Initialize date picker
                setupDatePicker();
            }, 300); // Increased delay to ensure everything is loaded
        },
        hide: () => {
            console.log('Hiding shipping modal');
            modal.style.display = 'none';
        },
        getFormData: () => {
            const name = document.getElementById('customer-name')?.value || '';
            const address = document.getElementById('customer-address')?.value || '';
            const email = document.getElementById('customer-email')?.value || '';
            const receivedByDate = document.getElementById('received-by-date')?.value || '';
            
            console.log('Form data collected:', { name, address, email, receivedByDate });
            
            return {
                name,
                address,
                email,
                receivedByDate
            };
        }
    };
    
    console.log('Shipping modal initialized');
    return modalObj;
};

// Initialize and export the modal
console.log('Creating shipping modal...');
window.shippingModal = createShippingModal();
console.log('Shipping modal created and assigned to window.shippingModal');