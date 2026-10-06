/**
 * bill_editor.js — Add/remove item rows in the bill review form.
 * Handles grand total recalculation, live cash tender calculation,
 * payment tab switching (Cash / UPI / Card), and confirmation with payment details.
 */

// ── Grand total recalculation ────────────────────────────
function recalcTotal() {
  const rows = document.querySelectorAll('#items-body .item-row');
  let grand = 0;

  rows.forEach(function (row) {
    const qty   = parseFloat(row.querySelector('.qty-input').value)   || 0;
    const price = parseFloat(row.querySelector('.price-input').value) || 0;
    const total = qty * price;
    const totalCell = row.querySelector('.row-total');
    if (totalCell) totalCell.textContent = '₹' + total.toFixed(2);
    grand += total;
  });

  const grandEl = document.getElementById('grand-total');
  if (grandEl) grandEl.textContent = '₹' + grand.toFixed(2);

  const upiPayEl = document.getElementById('upi-pay-amount');
  if (upiPayEl) upiPayEl.textContent = '₹' + grand.toFixed(2);

  const cardPayEl = document.getElementById('card-pay-amount');
  if (cardPayEl) cardPayEl.textContent = '₹' + grand.toFixed(2);

  // Recalculate cash change if tendered
  recalcCashChange(grand);
}

// ── Cash tender calculation ──────────────────────────────
function recalcCashChange(currentGrandTotal) {
  const tenderedInput = document.getElementById('cash_tendered');
  const changeEl = document.getElementById('cash_change');
  if (!tenderedInput || !changeEl) return;

  const tendered = parseFloat(tenderedInput.value) || 0;
  if (tendered > 0) {
    const change = tendered - currentGrandTotal;
    if (change >= 0) {
      changeEl.textContent = '₹' + change.toFixed(2);
      changeEl.style.color = '#15803d';
    } else {
      changeEl.textContent = 'Short by ₹' + Math.abs(change).toFixed(2);
      changeEl.style.color = '#dc2626';
    }
  } else {
    changeEl.textContent = '₹0.00';
    changeEl.style.color = 'inherit';
  }
}

const cashTenderInput = document.getElementById('cash_tendered');
if (cashTenderInput) {
  cashTenderInput.addEventListener('input', function () {
    const grandText = document.getElementById('grand-total').textContent.replace(/[^\d.]/g, '');
    const grand = parseFloat(grandText) || 0;
    recalcCashChange(grand);
  });
}

// ── Payment method switcher ──────────────────────────────
const paymentRadios = document.querySelectorAll('input[name="payment_method_choice"]');
const cashPanel = document.getElementById('cash-panel');
const upiPanel  = document.getElementById('upi-panel');
const cardPanel = document.getElementById('card-panel');

paymentRadios.forEach(function (radio) {
  radio.addEventListener('change', function () {
    if (cashPanel) cashPanel.style.display = (this.value === 'cash') ? 'block' : 'none';
    if (upiPanel)  upiPanel.style.display  = (this.value === 'upi')  ? 'block' : 'none';
    if (cardPanel) cardPanel.style.display = (this.value === 'card') ? 'block' : 'none';
  });
});

// ── Remove row ───────────────────────────────────────────
function bindRemoveButtons() {
  document.querySelectorAll('.remove-row').forEach(function (btn) {
    btn.onclick = function () {
      if (!confirm('Remove this item?')) return;
      btn.closest('.item-row').remove();
      recalcTotal();
    };
  });
}

// ── Add row ──────────────────────────────────────────────
const addBtn = document.getElementById('add-row-btn');
if (addBtn) {
  addBtn.addEventListener('click', function () {
    const tbody = document.getElementById('items-body');
    const row = document.createElement('tr');
    row.className = 'item-row';
    row.innerHTML = `
      <td><input type="text" name="product_name" class="form-input form-input--sm" placeholder="Product name" required></td>
      <td><input type="number" name="quantity"  class="form-input form-input--sm qty-input"   value="1"   min="0.01" step="0.01" required></td>
      <td><input type="number" name="unit_price" class="form-input form-input--sm price-input" value="0"   min="0"    step="0.01" required></td>
      <td class="row-total">₹0.00</td>
      <td></td>
      <td><button type="button" class="btn btn--sm btn--danger remove-row">✕</button></td>
    `;
    tbody.appendChild(row);
    bindRemoveButtons();

    // Focus the new product name field
    row.querySelector('input[name="product_name"]').focus();
  });
}

// ── Confirm bill ─────────────────────────────────────────
const confirmBtn  = document.getElementById('confirm-btn');
const confirmForm = document.getElementById('confirm-form');

if (confirmBtn && confirmForm) {
  confirmBtn.addEventListener('click', function () {
    if (document.querySelectorAll('#items-body .item-row').length === 0) {
      alert('Bill is empty. Add at least one item before confirming.');
      return;
    }

    // Get selected payment method
    const selectedMethod = document.querySelector('input[name="payment_method_choice"]:checked');
    const methodVal = selectedMethod ? selectedMethod.value : 'cash';

    // Get customer phone
    const phoneInput = document.getElementById('customer_phone_input');
    const phoneVal = phoneInput ? phoneInput.value.trim() : '';

    // Assign to hidden confirm form
    const hiddenMethod = document.getElementById('confirm_payment_method');
    if (hiddenMethod) hiddenMethod.value = methodVal;

    const hiddenPhone = document.getElementById('confirm_customer_phone');
    if (hiddenPhone) hiddenPhone.value = phoneVal;

    const methodName = methodVal === 'upi' ? 'UPI' : (methodVal === 'card' ? 'Card' : 'Cash');
    if (confirm(`Confirm and lock this bill settled via ${methodName}?`)) {
      confirmForm.submit();
    }
  });
}

// ── Live total recalc on input ───────────────────────────
document.addEventListener('input', function (e) {
  if (e.target.classList.contains('qty-input') ||
      e.target.classList.contains('price-input')) {
    recalcTotal();
  }
});

// ── Init ─────────────────────────────────────────────────
bindRemoveButtons();
recalcTotal();
