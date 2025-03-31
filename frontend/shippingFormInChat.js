// shippingFormInChat.js
// This adds an interactive shipping form directly into Plato's chat message box

const createShippingForm = () => {
    console.log('Initializing in-chat shipping form...');
    // Add these variables to track address validation
    let validAddresses = [];
    let hasValidAddress = false;

    // Add the CSS styles for the shipping form
    const addStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .shipping-form-container {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                width: 100%;
            }
            
            .shipping-form-header {
                margin: 0 0 15px 0;
                font-size: 16px;
                color: var(--secondary-color);
                font-weight: 500;
                text-align: center;
            }
        
            .shipping-form-group {
                margin-bottom: 15px;
                position: relative;
            }
            
            .shipping-form-label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: white;
                font-size: 14px;
            }
            
            .shipping-form-input {
                width: 100%;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 14px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            
            .shipping-form-input:focus {
                outline: none;
                border-color: var(--primary-color);
            }
            
            .shipping-form-input[readonly] {
                background-color: rgba(255, 255, 255, 0.05);
                cursor: pointer;
            }
            
            .date-input-container {
                position: relative;
                width: 100%;
            }
            
            .calendar-icon {
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                cursor: pointer;
                color: rgba(255, 255, 255, 0.7);
                font-size: 16px;
            }
            
            .address-suggestions {
                position: absolute;
                width: 100%;
                background: #333;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-top: none;
                border-radius: 0 0 4px 4px;
                z-index: 2050;
                max-height: 200px;
                overflow-y: auto;
                display: none;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            
            .suggestion-item {
                padding: 10px;
                cursor: pointer;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
            }
            
            .suggestion-item:last-child {
                border-bottom: none;
            }
            
            .suggestion-item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }

            /* Date Picker Styles */
            .date-picker-container {
                position: absolute;
                width: 320px;
                background: #333;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                z-index: 2050;
                display: none;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                padding: 10px;
                color: white;
            }
            
            .date-picker-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .date-picker-month {
                font-weight: bold;
                text-align: center;
                flex-grow: 1;
            }
            
            .date-picker-nav {
                cursor: pointer;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                color: white;
            }
            
            .date-picker-nav:hover {
                background: rgba(255, 255, 255, 0.2);
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
                color: rgba(255, 255, 255, 0.7);
            }
            
            .date-picker-days {
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 5px;
            }
            
            .date-picker-day {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 40px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                position: relative;
                padding: 2px 0;
            }
            
            .date-picker-day:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            .date-picker-day.active {
                background-color: var(--primary-color);
                color: white;
            }
            
            .date-picker-day.disabled {
                color: rgba(255, 255, 255, 0.3);
                cursor: not-allowed;
            }
            
            .date-picker-day.other-month {
                color: rgba(255, 255, 255, 0.4);
            }
            
            .shipping-form-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .shipping-form-cancel {
                padding: 8px 16px;
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
            }
            
            .shipping-form-submit {
                padding: 8px 16px;
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                flex: 1;
                margin-left: 10px;
                text-align: center;
            }
            
            .shipping-form-submit:disabled {
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            /* Style for the submitted form */
            .shipping-form-container.submitted input {
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.6);
            }
            
            .shipping-form-container.submitted .shipping-form-submit {
                background-color: #4CAF50;
            }
        `;
        document.head.appendChild(styleElement);
    };

    // Create the form elements (renamed from createShippingForm for clarity)
    const createShippingFormElements = (orderDetails) => {
        console.log('Creating shipping form with order details:', orderDetails);
        
        const container = document.createElement('div');
        container.className = 'shipping-form-container';
        
        // Header
        const header = document.createElement('div');
        header.className = 'shipping-form-header';
        header.textContent = 'Complete Your Order';
        container.appendChild(header);
        
        // Form
        const form = document.createElement('form');
        form.className = 'shipping-form';
        form.innerHTML = `
            <div class="shipping-form-group">
                <label class="shipping-form-label" for="customer-name">Full Name</label>
                <input type="text" id="customer-name" class="shipping-form-input" placeholder="Your full name" required>
            </div>
            
            <div class="shipping-form-group">
                <label class="shipping-form-label" for="customer-address">Shipping Address</label>
                <input type="text" id="customer-address" class="shipping-form-input" placeholder="Enter your shipping address" required>
                <div id="address-suggestions" class="address-suggestions"></div>
            </div>
            
            <div class="shipping-form-group">
                <label class="shipping-form-label" for="customer-email">Email for Invoice</label>
                <input type="email" id="customer-email" class="shipping-form-input" placeholder="Your email address" required>
            </div>
    
            <div class="shipping-form-group">
                <label class="shipping-form-label" for="received-by-date">Receive By Date</label>
                <div class="date-input-container">
                    <input type="text" id="received-by-date" class="shipping-form-input" readonly required>
                    <span class="calendar-icon">📅</span>
                </div>
                <div id="date-picker-container" class="date-picker-container"></div>
            </div>
        `;
        container.appendChild(form);
        
        // Footer with buttons
        const footer = document.createElement('div');
        footer.className = 'shipping-form-footer';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'shipping-form-cancel';
        cancelBtn.textContent = 'Cancel';
        
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'shipping-form-submit';
        submitBtn.textContent = 'Complete Order';
        
        footer.appendChild(cancelBtn);
        footer.appendChild(submitBtn);
        form.appendChild(footer);
        
        // Add event handlers
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            container.remove();
            
            // Re-enable chat if form is removed
            if (window.chatPermissions) {
                window.chatPermissions.enableChat();
            }
        });
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleFormSubmission(form, orderDetails);
            
            // Re-enable chat after form submission
            if (window.chatPermissions) {
                setTimeout(() => {
                    window.chatPermissions.enableChat();
                }, 300);
            }
        });
        
        // Setup form validation to manage chat permissions
        setupFormValidation(form);
        
        return { container, form };
    };
    
    // 3. Replace the setupFormValidation function with an updated version
    function setupFormValidation(form) {
        // This functionality is now handled directly in setupAddressAutocomplete
        // No further code needed here, but we're keeping the function for compatibility
    }
    
    // 4. Update the handleFormSubmission function to add a final address verification
    const handleFormSubmission = async (form, orderDetails) => {
        try {
            console.log('Handling form submission...');
            
            // Final address verification
            const addressInput = form.querySelector('#customer-address');
            const addressValue = addressInput.value.trim();
            const isValidAddress = validAddresses.includes(addressValue);
            
            if (!isValidAddress) {
                // Add an error message but don't submit
                const errorMsg = document.createElement('div');
                errorMsg.className = 'shipping-form-error';
                errorMsg.textContent = 'Please select a valid address from the suggestions list.';
                errorMsg.style.cssText = `
                    color: #f44336;
                    margin-top: 5px;
                    font-size: 14px;
                    text-align: center;
                    font-weight: bold;
                `;
                
                // Insert after submit button
                const footer = form.querySelector('.shipping-form-footer');
                if (footer) {
                    footer.parentNode.insertBefore(errorMsg, footer.nextSibling);
                    
                    // Scroll to make error visible
                    errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    
                    // Remove the error after 3 seconds
                    setTimeout(() => {
                        errorMsg.remove();
                    }, 3000);
                }
                
                return; // Don't proceed with submission
            }

            // Get form data
            const formData = {
                name: form.querySelector('#customer-name').value,
                address: addressValue,
                email: form.querySelector('#customer-email').value,
                receivedByDate: form.querySelector('#received-by-date').value
            };

            console.log('Form data collected:', formData);

            // Disable all form inputs instead of removing the form
            const formContainer = form.closest('.shipping-form-container');
            formContainer.querySelectorAll('input, button').forEach(element => {
                element.disabled = true;
            });

            // Change the submit button text and style to indicate completion
            const submitBtn = form.querySelector('.shipping-form-submit');
            if (submitBtn) {
                submitBtn.textContent = 'Order Submitted';
                submitBtn.style.backgroundColor = '#4CAF50';
            }

            // Add a "submitted" class to the container for any additional styling
            formContainer.classList.add('submitted');

            // Show a loading indicator
            const typingIndicator = addTypingIndicator();

            // Send data to backend
            const response = await fetch(`${API_BASE_URL}/api/submit-order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    name: formData.name,
                    address: formData.address,
                    email: formData.email,
                    receivedByDate: formData.receivedByDate
                }),
            });

            typingIndicator.remove();

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            const data = await response.json();

            // Display the response (order confirmation)
            if (data.text) {
                addMessage(data.text, 'bot');
            }

        } catch (error) {
            console.error('Error submitting order:', error);
            addMessage('Sorry, I encountered an error processing your order. Please try again.', 'bot');
        }
    };

    // Helper function to add a typing indicator
    const addTypingIndicator = () => {
        const indicator = document.createElement('div');
        indicator.className = 'message bot typing';
        indicator.textContent = 'Plato is typing...';
        document.getElementById('chat-messages').appendChild(indicator);
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        return indicator;
    };

    // Helper function to add a bot message
    const addMessage = (content, sender) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = content;
        document.getElementById('chat-messages').appendChild(messageDiv);
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        return messageDiv;
    };

    // Setup date picker
    const setupDatePicker = (form) => {
        console.log('Setting up date picker...');
        const dateInput = form.querySelector('#received-by-date');
        const datePickerContainer = form.querySelector('#date-picker-container');
        const calendarIcon = form.querySelector('.calendar-icon');

        if (!dateInput || !datePickerContainer) {
            console.error('Date picker elements not found!');
            return;
        }

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

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const freeShippingDate = new Date(today);
        freeShippingDate.setDate(today.getDate() + 17);

        let selectedDate = new Date(freeShippingDate);
        selectedDate.setHours(0, 0, 0, 0);

        const formatDate = (date) => {
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const year = date.getFullYear();
            return `${month}/${day}/${year}`;
        };

        dateInput.value = formatDate(selectedDate);

        const renderCalendar = () => {
            const daysContainer = datePickerContainer.querySelector('.date-picker-days');
            const monthDisplay = datePickerContainer.querySelector('.date-picker-month');

            if (!daysContainer || !monthDisplay) {
                console.error('Date picker elements not found!');
                return;
            }

            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
            monthDisplay.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;

            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            const firstDayOfWeek = firstDay.getDay();
            const totalDays = lastDay.getDate();

            daysContainer.innerHTML = '';

            const minShippingDate = new Date(today);
            minShippingDate.setDate(today.getDate() + 11);
            minShippingDate.setHours(0, 0, 0, 0);

            const tier1StartDate = new Date(today);
            tier1StartDate.setDate(today.getDate() + 15);
            tier1StartDate.setHours(0, 0, 0, 0);
            
            const tier1EndDate = new Date(today);
            tier1EndDate.setDate(today.getDate() + 16);
            tier1EndDate.setHours(0, 0, 0, 0);

            const tier2StartDate = new Date(today);
            tier2StartDate.setDate(today.getDate() + 13);
            tier2StartDate.setHours(0, 0, 0, 0);
            
            const tier2EndDate = new Date(today);
            tier2EndDate.setDate(today.getDate() + 14);
            tier2EndDate.setHours(0, 0, 0, 0);

            const tier3StartDate = new Date(today);
            tier3StartDate.setDate(today.getDate() + 11);
            tier3StartDate.setHours(0, 0, 0, 0);
            
            const tier3EndDate = new Date(today);
            tier3EndDate.setDate(today.getDate() + 12);
            tier3EndDate.setHours(0, 0, 0, 0);

            const isDateBetween = (date, startDate, endDate) => {
                const normalizedDate = new Date(date);
                normalizedDate.setHours(0, 0, 0, 0);
                
                const normalizedStartDate = new Date(startDate);
                normalizedStartDate.setHours(0, 0, 0, 0);
                
                const normalizedEndDate = new Date(endDate);
                normalizedEndDate.setHours(0, 0, 0, 0);
                
                return normalizedDate >= normalizedStartDate && normalizedDate <= normalizedEndDate;
            };

            const prevMonthLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();
            for (let i = 0; i < firstDayOfWeek; i++) {
                const dayDiv = document.createElement('div');
                dayDiv.className = 'date-picker-day other-month';
                dayDiv.textContent = prevMonthLastDay - firstDayOfWeek + i + 1;
                daysContainer.appendChild(dayDiv);
            }

            for (let i = 1; i <= totalDays; i++) {
                const dayDiv = document.createElement('div');
                dayDiv.className = 'date-picker-day';
                dayDiv.textContent = i;

                const dayDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), i);
                const normalizedDayDate = new Date(dayDate);
                normalizedDayDate.setHours(0, 0, 0, 0);

                if (normalizedDayDate < today || normalizedDayDate < minShippingDate) {
                    dayDiv.className += ' disabled';
                    dayDiv.title = 'Delivery not available for this date';
                } else {
                    let costIndicator = '';
                    let shippingTitle = '';

                    if (normalizedDayDate >= freeShippingDate) {
                        dayDiv.style.border = '2px solid #4CAF50';
                        dayDiv.style.backgroundColor = 'rgba(76, 175, 80, 0.2)';
                        shippingTitle = 'Standard shipping (no additional cost)';
                    }
                    else if (isDateBetween(normalizedDayDate, tier1StartDate, tier1EndDate)) {
                        costIndicator = '+10% Fee';
                        shippingTitle = 'Express shipping: +10% total order cost';
                        dayDiv.style.border = '1px solid #FFD700';
                        dayDiv.style.backgroundColor = 'rgba(255, 215, 0, 0.1)';
                    }
                    else if (isDateBetween(normalizedDayDate, tier2StartDate, tier2EndDate)) {
                        costIndicator = '+20% Fee';
                        shippingTitle = 'Express shipping: +20% total order cost';
                        dayDiv.style.border = '1px solid #FFA500';
                        dayDiv.style.backgroundColor = 'rgba(255, 165, 0, 0.1)';
                    }
                    else if (isDateBetween(normalizedDayDate, tier3StartDate, tier3EndDate)) {
                        costIndicator = '+30% Fee';
                        shippingTitle = 'Express shipping: +30% total order cost';
                        dayDiv.style.border = '1px solid #FF4500';
                        dayDiv.style.backgroundColor = 'rgba(255, 69, 0, 0.1)';
                    }

                    if (costIndicator) {
                        const costSpan = document.createElement('div');
                        costSpan.style.fontSize = '10px';
                        costSpan.style.color = 'rgba(255, 255, 255, 0.8)';
                        costSpan.style.marginTop = '2px';
                        costSpan.style.fontWeight = 'bold';
                        costSpan.textContent = costIndicator;
                        dayDiv.appendChild(costSpan);
                        dayDiv.title = shippingTitle;
                    }

                    if (selectedDate &&
                        selectedDate.getDate() === i &&
                        selectedDate.getMonth() === currentDate.getMonth() &&
                        selectedDate.getFullYear() === currentDate.getFullYear()) {
                        dayDiv.className += ' active';
                    }

                    dayDiv.addEventListener('click', () => {
                        selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), i);
                        selectedDate.setHours(0, 0, 0, 0);
                        dateInput.value = formatDate(selectedDate);
                        datePickerContainer.style.display = 'none';

                        if (costIndicator) {
                            showExpressShippingAlert(costIndicator, shippingTitle);
                        } else {
                            const existingAlert = form.querySelector('.express-shipping-alert');
                            if (existingAlert) {
                                existingAlert.remove();
                            }
                        }

                        renderCalendar();
                    });
                }

                daysContainer.appendChild(dayDiv);
            }

            const totalCellsUsed = firstDayOfWeek + totalDays;
            const cellsToFill = Math.ceil(totalCellsUsed / 7) * 7 - totalCellsUsed;

            for (let i = 1; i <= cellsToFill; i++) {
                const dayDiv = document.createElement('div');
                dayDiv.className = 'date-picker-day other-month';
                dayDiv.textContent = i;
                daysContainer.appendChild(dayDiv);
            }

            console.log(`Date picker debug info: 
                Today's reference date: ${today.toISOString()} (normalized to midnight)
                Free shipping date: ${freeShippingDate.toISOString()} (today + 17 days)
                Tier 1 range (+10%): ${tier1StartDate.toISOString()} to ${tier1EndDate.toISOString()}
                Tier 2 range (+20%): ${tier2StartDate.toISOString()} to ${tier2EndDate.toISOString()}
                Tier 3 range (+30%): ${tier3StartDate.toISOString()} to ${tier3EndDate.toISOString()}
                Selected date: ${selectedDate ? selectedDate.toISOString() : 'none'}`);
        };

        const showExpressShippingAlert = (costIndicator, shippingTitle) => {
            const existingAlert = form.querySelector('.express-shipping-alert');
            if (existingAlert) {
                existingAlert.remove();
            }

            const alertElement = document.createElement('div');
            alertElement.className = 'express-shipping-alert';
            alertElement.style.cssText = `
                margin-top: 10px;
                padding: 10px;
                background-color: rgba(255, 152, 0, 0.2);
                border: 1px solid #FF9800;
                border-radius: 4px;
                font-size: 14px;
                color: white;
                text-align: center;
            `;

            const percentage = costIndicator.match(/\d+/)[0];

            let costMessage = '';
            if (orderDetails && orderDetails.total) {
                const orderTotal = parseFloat(orderDetails.total);
                const expressCharge = orderTotal * (parseInt(percentage) / 100);
                const newTotal = orderTotal + expressCharge;
                costMessage = ` (approximately $${expressCharge.toFixed(2)}, making the new total $${newTotal.toFixed(2)})`;
            }

            alertElement.innerHTML = `
                <strong>Express Shipping Selected</strong><br>
                This delivery date adds ${costIndicator} to your order total${costMessage}.<br>
                <span style="font-size: 12px;">The additional charge covers expedited manufacturing and shipping.</span>
            `;

            const dateGroup = form.querySelector('.shipping-form-group:nth-child(4)');
            if (dateGroup) {
                dateGroup.appendChild(alertElement);
            }
        };

        const prevMonthBtn = datePickerContainer.querySelector('.date-picker-nav.prev');
        if (prevMonthBtn) {
            prevMonthBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1);
                renderCalendar();
            });
        }

        const nextMonthBtn = datePickerContainer.querySelector('.date-picker-nav.next');
        if (nextMonthBtn) {
            nextMonthBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
                renderCalendar();
            });
        }

        dateInput.addEventListener('click', (e) => {
            e.stopPropagation();
            const currentDisplay = window.getComputedStyle(datePickerContainer).display;

            if (currentDisplay === 'block') {
                datePickerContainer.style.display = 'none';
            } else {
                datePickerContainer.style.position = 'absolute';
                datePickerContainer.style.top = '100%';
                datePickerContainer.style.left = '0';
                datePickerContainer.style.zIndex = '9999';
                datePickerContainer.style.display = 'block';

                if (!selectedDate) {
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    currentDate = new Date(today.getFullYear(), today.getMonth(), 1);
                } else {
                    currentDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
                }

                renderCalendar();
            }
        });

        if (calendarIcon) {
            calendarIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                const currentDisplay = window.getComputedStyle(datePickerContainer).display;

                if (currentDisplay === 'block') {
                    datePickerContainer.style.display = 'none';
                } else {
                    datePickerContainer.style.position = 'absolute';
                    datePickerContainer.style.top = '100%';
                    datePickerContainer.style.left = '0';
                    datePickerContainer.style.zIndex = '9999';
                    datePickerContainer.style.display = 'block';

                    if (!selectedDate) {
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        currentDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    } else {
                        currentDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
                    }

                    renderCalendar();
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (datePickerContainer.style.display === 'block') {
                if (!e.target.closest('#received-by-date') &&
                    !e.target.closest('#date-picker-container') &&
                    !e.target.closest('.calendar-icon')) {
                    datePickerContainer.style.display = 'none';
                }
            }
        });

        renderCalendar();
    };

    // 2. Replace the setupAddressAutocomplete Function with the new implementation
    const setupAddressAutocomplete = (form) => {
        console.log('Setting up address autocomplete...');
        const addressInput = form.querySelector('#customer-address');
        const suggestionsContainer = form.querySelector('#address-suggestions');
        const submitBtn = form.querySelector('.shipping-form-submit');

        if (!addressInput || !suggestionsContainer) {
            console.error('Address autocomplete elements not found!');
            return;
        }

        // Add a validation status indicator next to the address field
        const validationIndicator = document.createElement('div');
        validationIndicator.style.cssText = `
            position: absolute;
            right: -30px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 20px;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        addressInput.parentNode.style.position = 'relative';
        addressInput.parentNode.appendChild(validationIndicator);

        const updateAddressValidation = (isValid) => {
            hasValidAddress = isValid;
            
            if (isValid) {
                validationIndicator.innerHTML = '✓';
                validationIndicator.style.color = '#4CAF50';
                addressInput.style.borderColor = '#4CAF50';
            } else {
                validationIndicator.innerHTML = '✗';
                validationIndicator.style.color = '#f44336';
                addressInput.style.borderColor = '#f44336';
            }
            
            // Update submit button state
            updateFormValidity();
        };

        addressInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            
            updateAddressValidation(false);

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
                    validAddresses = [];

                    if (data.suggestions && data.suggestions.length > 0) {
                        console.log(`Received ${data.suggestions.length} address suggestions`);
                        suggestionsContainer.style.display = 'block';

                        data.suggestions.forEach(suggestion => {
                            const addressText = suggestion.placePrediction.text.text;
                            validAddresses.push(addressText);
                            
                            const div = document.createElement('div');
                            div.className = 'suggestion-item';
                            div.textContent = addressText;

                            div.addEventListener('click', function() {
                                addressInput.value = addressText;
                                suggestionsContainer.style.display = 'none';
                                updateAddressValidation(true);
                            });

                            suggestionsContainer.appendChild(div);
                        });
                        
                        const exactMatch = validAddresses.includes(addressInput.value);
                        updateAddressValidation(exactMatch);
                        
                    } else {
                        console.log('No address suggestions received');
                        suggestionsContainer.style.display = 'none';
                        updateAddressValidation(false);
                    }
                })
                .catch(error => {
                    console.error('Error fetching autocomplete suggestions:', error);
                    suggestionsContainer.style.display = 'none';
                    updateAddressValidation(false);
                });
            }, 300);
        });

        addressInput.addEventListener('blur', function() {
            setTimeout(() => {
                const exactMatch = validAddresses.includes(this.value);
                updateAddressValidation(exactMatch);
            }, 200);
        });

        // Add the updateFormValidity function here (after the blur event)
        const updateFormValidity = () => {
            // Get all the other required inputs
            const nameInput = form.querySelector('#customer-name');
            const emailInput = form.querySelector('#customer-email');
            const dateInput = form.querySelector('#received-by-date');
            
            // Check if all fields have values and address is valid
            const isValid = nameInput.value.trim() !== '' && 
                            emailInput.value.trim() !== '' && 
                            dateInput.value.trim() !== '' &&
                            hasValidAddress;
            
            // Update submit button state
            if (submitBtn) {
                submitBtn.disabled = !isValid;
                submitBtn.style.opacity = isValid ? '1' : '0.7';
                submitBtn.style.cursor = isValid ? 'pointer' : 'not-allowed';
            }
            
            // If form is valid, disable chat to force completion
            if (isValid && window.chatPermissions) {
                window.chatPermissions.disableChat('Please complete your order information');
            }
        };

        document.addEventListener('click', function(e) {
            if (suggestionsContainer.style.display === 'block') {
                if (!e.target.closest('#customer-address') && !e.target.closest('#address-suggestions')) {
                    suggestionsContainer.style.display = 'none';
                }
            }
        });
    };

    // Main function to inject the shipping form into a message
    const injectShippingForm = (messageElement, orderDetails) => {
        console.log('Injecting shipping form into message:', messageElement);
        
        if (messageElement.querySelector('.shipping-form-container')) {
            console.log('Shipping form already injected, skipping');
            return;
        }
        
        if (window.chatPermissions) {
            window.chatPermissions.disableChat('Please complete your order information');
        }
        
        const { container, form } = createShippingFormElements(orderDetails);
        messageElement.appendChild(container);
        
        setTimeout(() => {
            setupDatePicker(form);
            setupAddressAutocomplete(form);
        }, 300);
    };

    // Monitor for messages with showShippingModal action
    const observeMessages = () => {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE &&
                            node.classList.contains('message') &&
                            node.classList.contains('bot')) {

                            if (node.dataset && node.dataset.action) {
                                try {
                                    const action = JSON.parse(node.dataset.action);
                                    if (action.type === 'showShippingModal') {
                                        console.log('Shipping modal action detected, injecting form');
                                        injectShippingForm(node, action.orderDetails);
                                    }
                                } catch (e) {
                                    console.error('Error parsing action data:', e);
                                }
                            }
                        }
                    });
                }
            });
        });

        observer.observe(chatMessages, { childList: true });

        return observer;
    };

    addStyles();
    const observer = observeMessages();

    return {
        injectIntoMessage: injectShippingForm,
        destroy: () => {
            if (observer) {
                observer.disconnect();
            }
        }
    };
};

console.log('Creating in-chat shipping form...');
window.shippingForm = createShippingForm();
console.log('In-chat shipping form created and assigned to window.shippingForm');