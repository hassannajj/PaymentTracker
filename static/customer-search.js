function wireCustomerSearch(inputId, datalistId, hiddenId, formId, amountInputId) {
    const input    = document.getElementById(inputId);
    const datalist = document.getElementById(datalistId);
    const hidden   = document.getElementById(hiddenId);
    const amountEl = amountInputId ? document.getElementById(amountInputId) : null;

    input.addEventListener('input', function () {
        hidden.value = '';
        for (const opt of datalist.options) {
            if (opt.value === this.value) {
                hidden.value = opt.getAttribute('data-id');
                if (amountEl) amountEl.value = opt.getAttribute('data-rate');
                break;
            }
        }
        if (!hidden.value && amountEl) amountEl.value = '';
    });

    document.getElementById(formId).addEventListener('submit', function (e) {
        if (!hidden.value) {
            e.preventDefault();
            alert('Please select a customer from the list.');
        }
    });
}

function wireCustomerFilter(inputId, rowSelector) {
    document.getElementById(inputId).addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll(rowSelector).forEach(row => {
            const name = row.dataset.customerName;
            const id   = row.dataset.customerId;
            row.style.display = (name.includes(q) || id.includes(q)) ? '' : 'none';
        });
    });
}
