const COUNTRY_CURRENCY = {
  Colombia: "COP",
  USA: "USD",
};

const dateFormatter = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });

const filterCountry = document.getElementById("filter-country");
const filterCategory = document.getElementById("filter-category");
const suppliersBody = document.getElementById("suppliers-body");
const supplierCount = document.getElementById("supplier-count");
const emptyState = document.getElementById("empty-state");
const errorAlert = document.getElementById("error-alert");
const statusMessage = document.getElementById("status-message");
const registerForm = document.getElementById("register-form");
const registerCountry = document.getElementById("register-country");
const registerCurrency = document.getElementById("register-currency");

function formatCategoryLabel(category) {
  return category.replaceAll("_", " ");
}

function formatCategories(categories) {
  return categories.map(formatCategoryLabel).join(", ");
}

function formatRate(rate, currency) {
  return `${rate.toLocaleString("en-US", {
    minimumFractionDigits: currency === "USD" ? 2 : 0,
    maximumFractionDigits: currency === "USD" ? 2 : 0,
  })} ${currency}`;
}

function formatTimestamp(value) {
  return dateFormatter.format(new Date(value));
}

function clearError() {
  errorAlert.hidden = true;
  errorAlert.textContent = "";
}

function showError(message) {
  statusMessage.hidden = true;
  statusMessage.textContent = "";
  errorAlert.hidden = false;
  errorAlert.textContent = message;
}

function showStatus(message) {
  clearError();
  statusMessage.hidden = false;
  statusMessage.textContent = message;
}

function renderErrorDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && typeof item.msg === "string") {
          return item.msg;
        }
        return String(item);
      })
      .join(" ");
  }

  if (detail && typeof detail === "object" && typeof detail.msg === "string") {
    return detail.msg;
  }

  return "Request failed.";
}

async function readErrorMessage(response) {
  try {
    const payload = await response.json();
    return renderErrorDetail(payload.detail);
  } catch {
    return "Request failed.";
  }
}

function syncRegisterCurrency() {
  registerCurrency.value = COUNTRY_CURRENCY[registerCountry.value] || "COP";
}

function getSelectedCategories(form) {
  return Array.from(form.querySelectorAll('input[name="categories"]:checked')).map(
    (input) => input.value,
  );
}

function updateSupplierRow(supplier) {
  const row = suppliersBody.querySelector(`tr[data-supplier-id="${supplier.id}"]`);
  if (!row) {
    return;
  }

  row.classList.toggle("row-suspended", supplier.status === "suspended");
  row.querySelector('[data-field="categories"]').textContent = formatCategories(
    supplier.categories,
  );
  row.querySelector('[data-field="rate"]').textContent = formatRate(
    supplier.rate_per_unit,
    supplier.currency,
  );
  row.querySelector('[data-field="status"]').innerHTML = renderStatusBadge(
    supplier.status,
  );
  row.querySelector('[data-field="contact"]').textContent =
    supplier.contact_email || "—";
  row.querySelector('[data-field="rate-updated"]').textContent = formatTimestamp(
    supplier.rate_updated_at,
  );

  const rateInput = row.querySelector(".inline-rate input");
  if (rateInput) {
    rateInput.value = String(supplier.rate_per_unit);
  }

  const toggleButton = row.querySelector(".btn-toggle");
  if (toggleButton) {
    toggleButton.textContent =
      supplier.status === "active" ? "Suspend" : "Activate";
    toggleButton.classList.toggle("suspend", supplier.status === "active");
    toggleButton.dataset.nextStatus =
      supplier.status === "active" ? "suspended" : "active";
  }
}

function renderStatusBadge(status) {
  return `<span class="status-badge ${status}">${status}</span>`;
}

function renderSupplierRow(supplier) {
  const row = document.createElement("tr");
  row.dataset.supplierId = String(supplier.id);
  row.classList.toggle("row-suspended", supplier.status === "suspended");

  row.innerHTML = `
    <td>${supplier.name}</td>
    <td>${supplier.country}</td>
    <td data-field="categories">${formatCategories(supplier.categories)}</td>
    <td data-field="rate">${formatRate(supplier.rate_per_unit, supplier.currency)}</td>
    <td data-field="status">${renderStatusBadge(supplier.status)}</td>
    <td data-field="contact">${supplier.contact_email || "—"}</td>
    <td data-field="rate-updated">${formatTimestamp(supplier.rate_updated_at)}</td>
    <td class="actions-cell">
      <div class="inline-rate">
        <input
          type="number"
          min="0.01"
          step="0.01"
          value="${supplier.rate_per_unit}"
          aria-label="New rate for ${supplier.name}"
        />
        <button type="button" class="btn-secondary update-rate-btn">Update rate</button>
      </div>
      <button
        type="button"
        class="btn-toggle ${supplier.status === "active" ? "suspend" : ""}"
        data-next-status="${supplier.status === "active" ? "suspended" : "active"}"
      >
        ${supplier.status === "active" ? "Suspend" : "Activate"}
      </button>
    </td>
  `;

  const updateRateButton = row.querySelector(".update-rate-btn");
  updateRateButton.addEventListener("click", async () => {
    const rateInput = row.querySelector(".inline-rate input");
    const newRate = Number(rateInput.value);

    clearError();
    const response = await fetch(`/suppliers/${supplier.id}/rate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rate_per_unit: newRate }),
    });

    if (!response.ok) {
      showError(await readErrorMessage(response));
      return;
    }

    const updated = await response.json();
    updateSupplierRow(updated);
    showStatus(`Rate updated for ${updated.name}.`);
  });

  const toggleButton = row.querySelector(".btn-toggle");
  toggleButton.addEventListener("click", async () => {
    clearError();
    const nextStatus = toggleButton.dataset.nextStatus;

    const response = await fetch(`/suppliers/${supplier.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: nextStatus }),
    });

    if (!response.ok) {
      showError(await readErrorMessage(response));
      return;
    }

    const updated = await response.json();
    updateSupplierRow(updated);
    showStatus(`${updated.name} is now ${updated.status}.`);
  });

  return row;
}

function renderSuppliers(suppliers) {
  suppliersBody.innerHTML = "";

  if (suppliers.length === 0) {
    emptyState.hidden = false;
    supplierCount.textContent = "0 suppliers";
    return;
  }

  emptyState.hidden = true;
  supplierCount.textContent = `${suppliers.length} supplier${
    suppliers.length === 1 ? "" : "s"
  }`;

  for (const supplier of suppliers) {
    suppliersBody.appendChild(renderSupplierRow(supplier));
  }
}

async function loadSuppliers(country = "", category = "") {
  clearError();
  supplierCount.textContent = "Loading suppliers…";

  const params = new URLSearchParams();
  if (country) {
    params.set("country", country);
  }
  if (category) {
    params.set("category", category);
  }

  const url = params.toString() ? `/suppliers?${params.toString()}` : "/suppliers";
  const response = await fetch(url);

  if (!response.ok) {
    showError(await readErrorMessage(response));
    suppliersBody.innerHTML = "";
    emptyState.hidden = true;
    supplierCount.textContent = "Unable to load suppliers";
    return;
  }

  const suppliers = await response.json();
  renderSuppliers(suppliers);
}

filterCountry.addEventListener("change", () => {
  loadSuppliers(filterCountry.value, filterCategory.value);
});

filterCategory.addEventListener("change", () => {
  loadSuppliers(filterCountry.value, filterCategory.value);
});

registerCountry.addEventListener("change", syncRegisterCurrency);

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const formData = new FormData(registerForm);
  const categories = getSelectedCategories(registerForm);

  const payload = {
    name: String(formData.get("name") || "").trim(),
    country: String(formData.get("country") || ""),
    categories,
    rate_per_unit: Number(formData.get("rate_per_unit")),
    currency: String(formData.get("currency") || ""),
    status: String(formData.get("status") || ""),
    contact_email: String(formData.get("contact_email") || "").trim() || null,
    notes: String(formData.get("notes") || "").trim() || null,
  };

  const response = await fetch("/suppliers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    showError(await readErrorMessage(response));
    return;
  }

  registerForm.reset();
  syncRegisterCurrency();
  registerCountry.value = "Colombia";
  registerCurrency.value = "COP";
  registerForm.querySelector('[name="status"]').value = "active";

  showStatus("Supplier registered successfully.");
  await loadSuppliers(filterCountry.value, filterCategory.value);
});

syncRegisterCurrency();
loadSuppliers();
