const VALID_STATUSES = ['open', 'in_progress', 'resolved', 'discarded'];

const CATEGORY_LABELS = {
  QUEJA_CLIENTE: 'Customer Complaint',
  EQUIPAMIENTO: 'Equipment',
  ABASTECIMIENTO: 'Supply',
  CALIDAD_ALIMENTO: 'Food Quality',
  PERSONAL: 'Staff',
};

function categoryLabel(code) {
  return CATEGORY_LABELS[code] ?? code;
}

const registerForm = document.getElementById('register-form');
const registerSubmit = document.getElementById('register-submit');
const registerOrigin = document.getElementById('register-origin');
const registerBranchField = document.getElementById('register-branch-field');
const branchHelper = document.getElementById('branch-helper');
const registerError = document.getElementById('register-error');
const registerSuccess = document.getElementById('register-success');

const filterStatus = document.getElementById('filter-status');
const filterOrigin = document.getElementById('filter-origin');
const filterBranch = document.getElementById('filter-branch');
const incidentCount = document.getElementById('incident-count');
const incidentsBody = document.getElementById('incidents-body');
const listEmptyState = document.getElementById('list-empty-state');
const listError = document.getElementById('list-error');
const listErrorMessage = document.getElementById('list-error-message');
const listRetry = document.getElementById('list-retry');
const listPagination = document.getElementById('list-pagination');
const listPrev = document.getElementById('list-prev');
const listNext = document.getElementById('list-next');
const listPageInfo = document.getElementById('list-page-info');

const summaryStatus = document.getElementById('summary-status');
const summaryError = document.getElementById('summary-error');
const summaryErrorMessage = document.getElementById('summary-error-message');
const summaryRetry = document.getElementById('summary-retry');
const summaryContent = document.getElementById('summary-content');
const summaryEmptyState = document.getElementById('summary-empty-state');
const summaryTotal = document.getElementById('summary-total');
const summaryByStatus = document.getElementById('summary-by-status');
const summaryByCategory = document.getElementById('summary-by-category');
const summaryByOrigin = document.getElementById('summary-by-origin');
const summaryByBranch = document.getElementById('summary-by-branch');

const FIELD_ERROR_IDS = {
  title: 'error-title',
  description: 'error-description',
  category: 'error-category',
  status: 'error-status',
  origin: 'error-origin',
  branch: 'error-branch',
};

let lastGoodIncidents = [];
let hasLoadedIncidents = false;
let listLoading = false;
let currentPage = 1;
const pageSize = 25;

function clearRegisterFieldErrors() {
  for (const elementId of Object.values(FIELD_ERROR_IDS)) {
    const element = document.getElementById(elementId);
    element.hidden = true;
    element.textContent = '';
  }
}

function clearRegisterBanners() {
  registerError.hidden = true;
  registerError.textContent = '';
  registerSuccess.hidden = true;
  registerSuccess.textContent = '';
}

function showRegisterError(message) {
  registerSuccess.hidden = true;
  registerSuccess.textContent = '';
  registerError.hidden = false;
  registerError.textContent = message;
}

function showRegisterSuccess(message) {
  registerError.hidden = true;
  registerError.textContent = '';
  registerSuccess.hidden = false;
  registerSuccess.textContent = message;
}

function applyFieldErrors(errors) {
  clearRegisterFieldErrors();
  for (const error of errors) {
    const elementId = FIELD_ERROR_IDS[error.field];
    if (!elementId) {
      continue;
    }
    const element = document.getElementById(elementId);
    element.hidden = false;
    element.textContent = error.message;
  }
}

function friendlyErrorMessage() {
  return 'Something went wrong. Please try again.';
}

function syncBranchHighlight() {
  const highlightBranch = registerOrigin.value === 'branch';
  registerBranchField.classList.toggle('field-highlighted', highlightBranch);
  branchHelper.hidden = !highlightBranch;
}

function setRegisterLoading(isLoading) {
  registerSubmit.disabled = isLoading;
  registerSubmit.textContent = isLoading ? 'Registering…' : 'Register incident';
}

function renderSummaryList(container, entries, formatLabel) {
  container.replaceChildren();
  const sortedEntries = Object.entries(entries).sort(([left], [right]) =>
    left.localeCompare(right),
  );

  if (sortedEntries.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'None';
    container.appendChild(item);
    return;
  }

  for (const [key, count] of sortedEntries) {
    const item = document.createElement('li');
    const name = document.createElement('span');
    const value = document.createElement('strong');
    name.textContent = formatLabel ? formatLabel(key) : key;
    value.textContent = String(count);
    item.append(name, value);
    container.appendChild(item);
  }
}

function formatIncidentRange(totalCount, pageIncidents) {
  if (totalCount === 0) {
    return '0 incidents';
  }

  const startIndex = (currentPage - 1) * pageSize + 1;
  const endIndex = startIndex + pageIncidents.length - 1;
  return `Showing ${startIndex}–${endIndex} of ${totalCount}`;
}

function updatePaginationControls(totalCount) {
  if (totalCount === 0) {
    listPagination.hidden = true;
    return;
  }

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  if (currentPage > totalPages) {
    currentPage = totalPages;
  }

  listPagination.hidden = totalPages <= 1;
  listPageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  listPrev.disabled = currentPage <= 1;
  listNext.disabled = currentPage >= totalPages;
}

function renderIncidents(incidents) {
  incidentsBody.replaceChildren();

  const filtersActive =
    Boolean(filterStatus.value) || Boolean(filterOrigin.value) || Boolean(filterBranch.value);

  if (incidents.length === 0) {
    listEmptyState.hidden = false;
    listEmptyState.textContent = hasLoadedIncidents
      ? filtersActive
        ? 'No incidents match the current filters.'
        : 'No incidents recorded yet. Register one above.'
      : 'No incidents recorded yet. Register one above.';
    incidentCount.textContent = '0 incidents';
    listPagination.hidden = true;
    return;
  }

  listEmptyState.hidden = true;
  updatePaginationControls(incidents.length);

  const startIndex = (currentPage - 1) * pageSize;
  const pageIncidents = incidents.slice(startIndex, startIndex + pageSize);
  incidentCount.textContent = formatIncidentRange(incidents.length, pageIncidents);

  for (const incident of pageIncidents) {
    const row = document.createElement('tr');
    row.dataset.incidentId = String(incident.id);

    const titleCell = document.createElement('td');
    const title = document.createElement('div');
    title.className = 'incident-title';
    title.textContent = incident.title;
    const description = document.createElement('p');
    description.className = 'incident-description';
    description.textContent = incident.description;
    titleCell.append(title, description);

    const categoryCell = document.createElement('td');
    categoryCell.textContent = categoryLabel(incident.category);

    const branchCell = document.createElement('td');
    branchCell.textContent = incident.branch;

    const originCell = document.createElement('td');
    originCell.textContent = incident.origin;

    const statusCell = document.createElement('td');
    const statusSelect = document.createElement('select');
    statusSelect.className = 'status-select';
    statusSelect.setAttribute('aria-label', `Update status for ${incident.title}`);

    for (const status of VALID_STATUSES) {
      const option = document.createElement('option');
      option.value = status;
      option.textContent = status;
      option.selected = status === incident.status;
      statusSelect.appendChild(option);
    }

    statusSelect.addEventListener('change', async () => {
      const previousStatus = incident.status;
      const nextStatus = statusSelect.value;
      incident.status = nextStatus;

      const response = await fetch(`/api/incidents/${incident.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });

      if (!response.ok) {
        statusSelect.value = previousStatus;
        incident.status = previousStatus;
        listErrorMessage.textContent =
          'That status change is not allowed. The previous status has been restored.';
        listError.hidden = false;
        return;
      }

      const updated = await response.json();
      incident.status = updated.status;
      statusSelect.value = updated.status;
      listError.hidden = true;
      await loadSummary();
    });

    statusCell.appendChild(statusSelect);

    row.append(titleCell, categoryCell, branchCell, originCell, statusCell);
    incidentsBody.appendChild(row);
  }
}

function showListError(message) {
  listErrorMessage.textContent = message;
  listError.hidden = false;
}

function hideListError() {
  listError.hidden = true;
  listErrorMessage.textContent = '';
}

async function loadIncidents() {
  if (listLoading) {
    return;
  }

  listLoading = true;
  hideListError();
  incidentCount.textContent = 'Loading incidents…';

  const params = new URLSearchParams();
  if (filterStatus.value) {
    params.set('status', filterStatus.value);
  }
  if (filterOrigin.value) {
    params.set('origin', filterOrigin.value);
  }
  if (filterBranch.value) {
    params.set('branch', filterBranch.value);
  }

  const url = params.toString() ? `/api/incidents?${params.toString()}` : '/api/incidents';

  try {
    const response = await fetch(url);
    if (!response.ok) {
      showListError('Unable to load incidents right now.');
      incidentCount.textContent = 'Unable to load incidents';
      if (hasLoadedIncidents) {
        renderIncidents(lastGoodIncidents);
      }
      return;
    }

    const incidents = await response.json();
    lastGoodIncidents = incidents;
    hasLoadedIncidents = true;
    renderIncidents(incidents);
  } catch {
    showListError('Unable to load incidents right now.');
    incidentCount.textContent = 'Unable to load incidents';
    if (hasLoadedIncidents) {
      renderIncidents(lastGoodIncidents);
    }
  } finally {
    listLoading = false;
  }
}

function showSummaryError(message) {
  summaryErrorMessage.textContent = message;
  summaryError.hidden = false;
  summaryStatus.textContent = 'Summary unavailable';
}

function hideSummaryError() {
  summaryError.hidden = true;
  summaryErrorMessage.textContent = '';
}

async function loadSummary() {
  hideSummaryError();
  summaryStatus.textContent = 'Loading summary…';
  summaryContent.hidden = true;
  summaryEmptyState.hidden = true;

  try {
    const response = await fetch('/api/incidents/summary');
    if (!response.ok) {
      showSummaryError('Unable to load summary metrics right now.');
      return;
    }

    const summary = await response.json();
    summaryTotal.textContent = String(summary.total);
    renderSummaryList(summaryByStatus, summary.by_status);
    renderSummaryList(summaryByCategory, summary.by_category, categoryLabel);
    renderSummaryList(summaryByOrigin, summary.by_origin);
    renderSummaryList(summaryByBranch, summary.by_branch);

    if (summary.total === 0) {
      summaryEmptyState.hidden = false;
      summaryContent.hidden = true;
      summaryStatus.textContent = 'No summary data yet';
      return;
    }

    summaryContent.hidden = false;
    summaryEmptyState.hidden = true;
    summaryStatus.textContent = `${summary.total} incidents tracked`;
  } catch {
    showSummaryError('Unable to load summary metrics right now.');
  }
}

registerOrigin.addEventListener('change', syncBranchHighlight);

registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearRegisterBanners();
  clearRegisterFieldErrors();
  setRegisterLoading(true);

  const formData = new FormData(registerForm);
  const payload = {
    title: String(formData.get('title') || '').trim(),
    description: String(formData.get('description') || '').trim(),
    category: String(formData.get('category') || ''),
    status: String(formData.get('status') || 'open'),
    origin: String(formData.get('origin') || ''),
    branch: String(formData.get('branch') || ''),
  };

  try {
    const response = await fetch('/api/incidents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.status === 400) {
      const body = await response.json();
      const errors = body.detail?.errors;
      if (Array.isArray(errors) && errors.length > 0) {
        applyFieldErrors(errors);
      } else {
        showRegisterError('Please check the form and try again.');
      }
      return;
    }

    if (!response.ok) {
      showRegisterError(friendlyErrorMessage());
      return;
    }

    registerForm.reset();
    registerForm.querySelector('[name="status"]').value = 'open';
    syncBranchHighlight();
    showRegisterSuccess('Incident registered successfully.');
    await Promise.all([loadIncidents(), loadSummary()]);
  } catch {
    showRegisterError(friendlyErrorMessage());
  } finally {
    setRegisterLoading(false);
  }
});

filterStatus.addEventListener('change', () => {
  currentPage = 1;
  loadIncidents();
});

filterOrigin.addEventListener('change', () => {
  currentPage = 1;
  loadIncidents();
});

filterBranch.addEventListener('change', () => {
  currentPage = 1;
  loadIncidents();
});

listPrev.addEventListener('click', () => {
  if (currentPage > 1) {
    currentPage -= 1;
    renderIncidents(lastGoodIncidents);
  }
});

listNext.addEventListener('click', () => {
  const totalPages = Math.ceil(lastGoodIncidents.length / pageSize);
  if (currentPage < totalPages) {
    currentPage += 1;
    renderIncidents(lastGoodIncidents);
  }
});

listRetry.addEventListener('click', () => {
  loadIncidents();
});

summaryRetry.addEventListener('click', () => {
  loadSummary();
});

syncBranchHighlight();
loadIncidents();
loadSummary();
