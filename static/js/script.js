document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Product search functionality
    const productSearchInput = document.getElementById('productSearch');
    if (productSearchInput) {
        productSearchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const productRows = document.querySelectorAll('table tbody tr');
            
            productRows.forEach(row => {
                const productName = row.querySelector('td:first-child').textContent.toLowerCase();
                const categoryName = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                
                if (productName.includes(searchValue) || categoryName.includes(searchValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Sales page - calculate total when quantity changes
    const quantityInput = document.getElementById('quantity');
    const unitPriceDisplay = document.getElementById('unit-price');
    const totalPriceDisplay = document.getElementById('total-price');
    
    if (quantityInput && unitPriceDisplay && totalPriceDisplay) {
        quantityInput.addEventListener('input', updateTotalPrice);
        
        function updateTotalPrice() {
            const quantity = parseInt(quantityInput.value) || 0;
            const unitPrice = parseFloat(unitPriceDisplay.value) || 0;
            const total = quantity * unitPrice;
            totalPriceDisplay.value = total.toFixed(2);
        }
    }
    
    // Print functionality for reports and invoices
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });
    
    // Automatically set selling price based on purchase price with margin
    const purchasePriceInput = document.getElementById('purchase_price');
    const sellingPriceInput = document.getElementById('selling_price');
    const marginPercentInput = document.getElementById('margin_percent');
    
    if (purchasePriceInput && sellingPriceInput) {
        purchasePriceInput.addEventListener('input', function() {
            // Only auto-calculate if selling price is empty or margin percent exists
            if (sellingPriceInput.value === '' || (marginPercentInput && marginPercentInput.value !== '')) {
                const purchasePrice = parseFloat(this.value) || 0;
                const marginPercent = marginPercentInput ? (parseFloat(marginPercentInput.value) || 40) : 40;
                const sellingPrice = purchasePrice * (1 + marginPercent / 100);
                sellingPriceInput.value = sellingPrice.toFixed(2);
            }
        });
        
        if (marginPercentInput) {
            marginPercentInput.addEventListener('input', function() {
                const purchasePrice = parseFloat(purchasePriceInput.value) || 0;
                const marginPercent = parseFloat(this.value) || 0;
                const sellingPrice = purchasePrice * (1 + marginPercent / 100);
                sellingPriceInput.value = sellingPrice.toFixed(2);
            });
        }
    }
    
    // Expense date defaults to today
    const expenseDateInput = document.getElementById('expense_date');
    if (expenseDateInput && !expenseDateInput.value) {
        const today = new Date();
        const formattedDate = today.toISOString().substr(0, 10);
        expenseDateInput.value = formattedDate;
    }
    
    // Sale date defaults to today
    const saleDateInput = document.getElementById('sale_date');
    if (saleDateInput && !saleDateInput.value) {
        const today = new Date();
        const formattedDate = today.toISOString().substr(0, 10);
        saleDateInput.value = formattedDate;
    }
});
