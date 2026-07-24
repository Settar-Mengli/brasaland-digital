const COUNTRY_CURRENCY = {
  Colombia: 'COP',
  USA: 'USD',
};

const dateFormatter = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' });

let expandedSupplierId = null;

const filterCountry = document.getElementById('filter-country');
const filterCategory = document.getElementById('filter-category');
const suppliersList = document.getElementById('suppliers-list');
const supplierCount = document.getElementById('supplier-count');
const emptyState = document.getElementById('empty-state');
const errorAlert = document.getElementById('error-alert');
const statusMessage = document.getElementById('status-message');
const registerForm = document.getElementById('register-form');
const registerCountry = document.getElementById('register-country');
const registerCurrency = document.getElementById('register-currency');

function formatCategoryLabel(category) {
  return category.replaceAll('_', ' ');
}

function formatCategories(categories) {
  return categories.map(formatCategoryLabel).join(', ');
}

function formatRate(rate, currency) {
  return `${rate.toLocaleString('en-US', {
    minimumFractionDigits: currency === 'USD' ? 2 : 0,
    maximumFractionDigits: currency === 'USD' ? 2 : 0,
  })} ${currency}`;
}

function formatTimestamp(value) {
  return dateFormatter.format(new Date(value));
}

function clearError() {
  errorAlert.hidden = true;
  errorAlert.textContent = '';
}

function showError(message) {
  statusMessage.hidden = true;
  statusMessage.textContent = '';
  errorAlert.hidden = false;
  errorAlert.textContent = message;
}

function showStatus(message) {
  clearError();
  statusMessage.hidden = false;
  statusMessage.textContent = message;
}

function renderErrorDetail(detail) {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }
        if (item && typeof item === 'object' && typeof item.msg === 'string') {
          return item.msg;
        }
        return String(item);
      })
      .join(' ');
  }

  if (detail && typeof detail === 'object' && typeof detail.msg === 'string') {
    return detail.msg;
  }

  return 'Request failed.';
}

async function readErrorMessage(response) {
  try {
    const payload = await response.json();
    return renderErrorDetail(payload.detail);
  } catch {
    return 'Request failed.';
  }
}

function syncRegisterCurrency() {
  registerCurrency.value = COUNTRY_CURRENCY[registerCountry.value] || 'COP';
}

function getSelectedCategories(form) {
  return Array.from(form.querySelectorAll('input[name="categories"]:checked')).map(
    (input) => input.value,
  );
}

function setStatusBadge(container, status) {
  container.replaceChildren();
  const badge = document.createElement('span');
  badge.className = `status-badge ${status}`;
  badge.textContent = status;
  container.appendChild(badge);
}

function renderCategoryChips(container, categories) {
  container.replaceChildren();
  const wrapper = document.createElement('div');
  wrapper.className = 'category-chips';

  for (const category of categories) {
    const chip = document.createElement('span');
    chip.className = 'category-chip';
    chip.textContent = formatCategoryLabel(category);
    wrapper.appendChild(chip);
  }

  container.appendChild(wrapper);
}

function collapseSupplierItem(item) {
  const toggle = item.querySelector('.supplier-toggle');
  const detail = item.querySelector('.supplier-detail');
  const name = item.querySelector('.supplier-name')?.textContent || 'supplier';

  item.classList.remove('is-expanded');
  if (toggle) {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', `Show details for ${name}`);
  }
  if (detail) {
    detail.hidden = true;
  }
}

function expandSupplierItem(item) {
  for (const other of suppliersList.querySelectorAll('.supplier-item.is-expanded')) {
    if (other !== item) {
      collapseSupplierItem(other);
    }
  }

  const toggle = item.querySelector('.supplier-toggle');
  const detail = item.querySelector('.supplier-detail');
  const name = item.querySelector('.supplier-name')?.textContent || 'supplier';

  item.classList.add('is-expanded');
  if (toggle) {
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', `Hide details for ${name}`);
  }
  if (detail) {
    detail.hidden = false;
  }

  expandedSupplierId = Number(item.dataset.supplierId);
}

function toggleSupplierItem(item) {
  if (item.classList.contains('is-expanded')) {
    collapseSupplierItem(item);
    expandedSupplierId = null;
    return;
  }

  expandSupplierItem(item);
}

function updateSupplierRow(supplier) {
  const item = suppliersList.querySelector(`.supplier-item[data-supplier-id="${supplier.id}"]`);
  if (!item) {
    return;
  }

  item.classList.toggle('row-suspended', supplier.status === 'suspended');

  const nameEl = item.querySelector('.supplier-name');
  if (nameEl) {
    nameEl.textContent = supplier.name;
  }

  const countryEl = item.querySelector('[data-field="country"]');
  if (countryEl) {
    countryEl.textContent = supplier.country;
  }

  const rateEl = item.querySelector('[data-field="rate"]');
  if (rateEl) {
    rateEl.textContent = formatRate(supplier.rate_per_unit, supplier.currency);
  }

  const statusEl = item.querySelector('[data-field="status"]');
  if (statusEl) {
    setStatusBadge(statusEl, supplier.status);
  }

  const categoriesEl = item.querySelector('[data-field="categories"]');
  if (categoriesEl) {
    renderCategoryChips(categoriesEl, supplier.categories);
  }

  const contactEl = item.querySelector('[data-field="contact"]');
  if (contactEl) {
    contactEl.textContent = supplier.contact_email || '—';
  }

  const rateUpdatedEl = item.querySelector('[data-field="rate-updated"]');
  if (rateUpdatedEl) {
    rateUpdatedEl.textContent = formatTimestamp(supplier.rate_updated_at);
  }

  const notesEl = item.querySelector('[data-field="notes"]');
  if (notesEl) {
    notesEl.textContent = supplier.notes || '—';
  }

  const rateInput = item.querySelector('.inline-rate input');
  if (rateInput) {
    rateInput.value = String(supplier.rate_per_unit);
    rateInput.setAttribute('aria-label', `New rate for ${supplier.name}`);
  }

  const currencyEl = item.querySelector(".inline-rate [data-field='currency']");
  if (currencyEl) {
    currencyEl.textContent = supplier.currency;
  }

  const toggleButton = item.querySelector('.btn-toggle');
  if (toggleButton) {
    const isActive = supplier.status === 'active';
    toggleButton.textContent = isActive ? 'Suspend' : 'Activate';
    toggleButton.classList.toggle('suspend', isActive);
    toggleButton.dataset.nextStatus = isActive ? 'suspended' : 'active';
    toggleButton.setAttribute(
      'aria-label',
      isActive ? `Suspend ${supplier.name}` : `Activate ${supplier.name}`,
    );
  }

  const expandToggle = item.querySelector('.supplier-toggle');
  if (expandToggle && !item.classList.contains('is-expanded')) {
    expandToggle.setAttribute('aria-label', `Show details for ${supplier.name}`);
  } else if (expandToggle) {
    expandToggle.setAttribute('aria-label', `Hide details for ${supplier.name}`);
  }
}

function renderSupplierItem(supplier) {
  const item = document.createElement('li');
  item.className = 'supplier-item';
  item.dataset.supplierId = String(supplier.id);
  item.classList.toggle('row-suspended', supplier.status === 'suspended');

  const detailId = `supplier-detail-${supplier.id}`;
  const nameId = `supplier-name-${supplier.id}`;
  const isActive = supplier.status === 'active';

  item.innerHTML = `
    <div class="supplier-summary">
      <button
        type="button"
        class="supplier-toggle"
        aria-expanded="false"
        aria-controls="${detailId}"
      >
        <span class="supplier-chevron" aria-hidden="true"></span>
      </button>
      <span id="${nameId}" class="supplier-name col-name"></span>
      <span class="col-country" data-field="country"></span>
      <span class="col-rate" data-field="rate"></span>
      <span class="col-status" data-field="status"></span>
    </div>
    <div
      id="${detailId}"
      class="supplier-detail"
      hidden
      role="region"
      aria-labelledby="${nameId}"
    >
      <dl class="supplier-detail-grid">
        <div class="detail-row">
          <dt>Categories</dt>
          <dd data-field="categories"></dd>
        </div>
        <div class="detail-row">
          <dt>Contact</dt>
          <dd data-field="contact"></dd>
        </div>
        <div class="detail-row">
          <dt>Rate updated</dt>
          <dd data-field="rate-updated"></dd>
        </div>
        <div class="detail-row">
          <dt>Notes</dt>
          <dd data-field="notes"></dd>
        </div>
      </dl>
      <div class="supplier-actions">
        <div class="inline-rate">
          <input
            type="number"
            min="0.01"
            step="0.01"
          />
          <span class="rate-currency-suffix" data-field="currency"></span>
          <button type="button" class="btn-secondary update-rate-btn">Update rate</button>
        </div>
        <button
          type="button"
          class="btn-toggle ${isActive ? 'suspend' : ''}"
          data-next-status="${isActive ? 'suspended' : 'active'}"
        >
          ${isActive ? 'Suspend' : 'Activate'}
        </button>
      </div>
    </div>
  `;

  item.querySelector('.supplier-name').textContent = supplier.name;
  item.querySelector('[data-field="country"]').textContent = supplier.country;
  item.querySelector('[data-field="rate"]').textContent = formatRate(
    supplier.rate_per_unit,
    supplier.currency,
  );
  setStatusBadge(item.querySelector('[data-field="status"]'), supplier.status);
  renderCategoryChips(item.querySelector('[data-field="categories"]'), supplier.categories);
  item.querySelector('[data-field="contact"]').textContent = supplier.contact_email || '—';
  item.querySelector('[data-field="rate-updated"]').textContent = formatTimestamp(
    supplier.rate_updated_at,
  );
  item.querySelector('[data-field="notes"]').textContent = supplier.notes || '—';

  const rateInput = item.querySelector('.inline-rate input');
  rateInput.value = String(supplier.rate_per_unit);
  rateInput.setAttribute('aria-label', `New rate for ${supplier.name}`);

  item.querySelector(".inline-rate [data-field='currency']").textContent = supplier.currency;

  const expandToggle = item.querySelector('.supplier-toggle');
  const toggleButton = item.querySelector('.btn-toggle');
  expandToggle.setAttribute('aria-label', `Show details for ${supplier.name}`);
  toggleButton.setAttribute(
    'aria-label',
    isActive ? `Suspend ${supplier.name}` : `Activate ${supplier.name}`,
  );

  expandToggle.addEventListener('click', () => {
    toggleSupplierItem(item);
  });

  const updateRateButton = item.querySelector('.update-rate-btn');
  updateRateButton.addEventListener('click', async () => {
    const input = item.querySelector('.inline-rate input');
    const newRate = Number(input.value);

    clearError();
    try {
      const response = await fetch(`/suppliers/${supplier.id}/rate`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rate_per_unit: newRate }),
      });

      if (!response.ok) {
        showError(await readErrorMessage(response));
        return;
      }

      const updated = await response.json();
      updateSupplierRow(updated);
      showStatus(`Rate updated for ${updated.name}.`);
    } catch {
      showError('Unable to reach the supplier directory. Please try again.');
    }
  });

  toggleButton.addEventListener('click', async () => {
    clearError();
    const nextStatus = toggleButton.dataset.nextStatus;

    try {
      const response = await fetch(`/suppliers/${supplier.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });

      if (!response.ok) {
        showError(await readErrorMessage(response));
        return;
      }

      const updated = await response.json();
      updateSupplierRow(updated);
      showStatus(`${updated.name} is now ${updated.status}.`);
    } catch {
      showError('Unable to reach the supplier directory. Please try again.');
    }
  });

  return item;
}

function renderSuppliers(suppliers) {
  suppliersList.replaceChildren();

  if (suppliers.length === 0) {
    emptyState.hidden = false;
    supplierCount.textContent = '0 suppliers';
    expandedSupplierId = null;
    return;
  }

  emptyState.hidden = true;
  supplierCount.textContent = `${suppliers.length} supplier${suppliers.length === 1 ? '' : 's'}`;

  for (const supplier of suppliers) {
    suppliersList.appendChild(renderSupplierItem(supplier));
  }

  if (expandedSupplierId !== null) {
    const item = suppliersList.querySelector(
      `.supplier-item[data-supplier-id="${expandedSupplierId}"]`,
    );
    if (item) {
      expandSupplierItem(item);
    } else {
      expandedSupplierId = null;
    }
  }
}

function resetSuppliersLoadFailure() {
  suppliersList.replaceChildren();
  emptyState.hidden = true;
  supplierCount.textContent = 'Unable to load suppliers';
}

async function loadSuppliers(country = '', category = '') {
  clearError();
  supplierCount.textContent = 'Loading suppliers…';

  const params = new URLSearchParams();
  if (country) {
    params.set('country', country);
  }
  if (category) {
    params.set('category', category);
  }

  const url = params.toString() ? `/suppliers?${params.toString()}` : '/suppliers';

  try {
    const response = await fetch(url);

    if (!response.ok) {
      showError(await readErrorMessage(response));
      resetSuppliersLoadFailure();
      return;
    }

    const suppliers = await response.json();
    renderSuppliers(suppliers);
  } catch {
    showError('Unable to reach the supplier directory. Please try again.');
    resetSuppliersLoadFailure();
  }
}

filterCountry.addEventListener('change', () => {
  loadSuppliers(filterCountry.value, filterCategory.value);
});

filterCategory.addEventListener('change', () => {
  loadSuppliers(filterCountry.value, filterCategory.value);
});

registerCountry.addEventListener('change', syncRegisterCurrency);

registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearError();

  const formData = new FormData(registerForm);
  const categories = getSelectedCategories(registerForm);

  const payload = {
    name: String(formData.get('name') || '').trim(),
    country: String(formData.get('country') || ''),
    categories,
    rate_per_unit: Number(formData.get('rate_per_unit')),
    currency: String(formData.get('currency') || ''),
    status: String(formData.get('status') || ''),
    contact_email: String(formData.get('contact_email') || '').trim() || null,
    notes: String(formData.get('notes') || '').trim() || null,
  };

  try {
    const response = await fetch('/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      showError(await readErrorMessage(response));
      return;
    }

    registerForm.reset();
    syncRegisterCurrency();
    registerCountry.value = 'Colombia';
    registerCurrency.value = 'COP';
    registerForm.querySelector('[name="status"]').value = 'active';

    showStatus('Supplier registered successfully.');
    await loadSuppliers(filterCountry.value, filterCategory.value);
  } catch {
    showError('Unable to reach the supplier directory. Please try again.');
  }
});

syncRegisterCurrency();
loadSuppliers();
