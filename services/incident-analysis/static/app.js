const RULE_LABELS = {
  invalid_location: 'Missing location_id',
  invalid_category: 'Invalid or missing category',
  invalid_description: 'Empty description',
  missing_reporter: 'Missing reporter_id',
  cerrado_missing_score: 'Closed case, no score',
  invalid_satisfaction_score: 'Invalid satisfaction score',
};

const CATEGORY_ORDER = [
  'QUEJA_CLIENTE',
  'EQUIPAMIENTO',
  'ABASTECIMIENTO',
  'CALIDAD_ALIMENTO',
  'PERSONAL',
];

const STATUS_ORDER = ['ABIERTO', 'CERRADO', 'DESCARTADO'];

const SCORE_LABELS = {
  1: 'Very dissatisfied',
  2: 'Dissatisfied',
  3: 'Neutral',
  4: 'Satisfied',
  5: 'Very satisfied',
};

const csvInput = document.getElementById('csv-file');
const dropZone = document.getElementById('drop-zone');
const selectedFileLabel = document.getElementById('selected-file');
const analyzeButton = document.getElementById('analyze-btn');
const downloadButton = document.getElementById('download-btn');
const errorAlert = document.getElementById('error-alert');
const loadingIndicator = document.getElementById('loading');
const summaryPanel = document.getElementById('summary');
const totalsGrid = document.getElementById('totals-grid');
const categoryTableBody = document.querySelector('#category-table tbody');
const statusTableBody = document.querySelector('#status-table tbody');
const satisfactionSection = document.getElementById('satisfaction-section');
const invalidRecordsList = document.getElementById('invalid-records');

let selectedFile = null;

function ruleLabel(ruleId) {
  return RULE_LABELS[ruleId] || ruleId.replaceAll('_', ' ');
}

function formatPercentage(count, total) {
  if (!total) {
    return 'N/A';
  }
  return `${((count / total) * 100).toFixed(1)}%`;
}

function showError(message) {
  errorAlert.hidden = false;
  errorAlert.textContent = message;
}

function clearError() {
  errorAlert.hidden = true;
  errorAlert.textContent = '';
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
        return 'Request failed.';
      })
      .join(' ');
  }

  if (detail && typeof detail === 'object' && typeof detail.msg === 'string') {
    return detail.msg;
  }

  return 'Request failed.';
}

function setLoading(isLoading) {
  loadingIndicator.hidden = !isLoading;
  analyzeButton.disabled = isLoading || !selectedFile;
}

function setSelectedFile(file) {
  selectedFile = file;
  selectedFileLabel.textContent = file ? file.name : '';
  analyzeButton.disabled = !file;
}

function renderTableBody(tbody, order, counts, validTotal) {
  tbody.innerHTML = '';
  for (const key of order) {
    const count = counts[key] ?? 0;
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${key}</td>
      <td>${count}</td>
      <td>${formatPercentage(count, validTotal)}</td>
    `;
    tbody.appendChild(row);
  }
}

function distributionCount(distribution, score) {
  return distribution[score] ?? distribution[String(score)] ?? 0;
}

function renderSummary(data) {
  const validTotal = data.totals.valid;
  const closedTotal = data.by_status.CERRADO ?? 0;

  totalsGrid.innerHTML = `
    <div class="total-card">
      <span>Total records</span>
      <strong>${data.totals.total}</strong>
    </div>
    <div class="total-card">
      <span>Valid records</span>
      <strong>${data.totals.valid}</strong>
    </div>
    <div class="total-card">
      <span>Invalid records</span>
      <strong>${data.totals.invalid}</strong>
    </div>
  `;

  renderTableBody(categoryTableBody, CATEGORY_ORDER, data.by_category, validTotal);
  renderTableBody(statusTableBody, STATUS_ORDER, data.by_status, validTotal);

  if (data.average_satisfaction_closed == null || closedTotal === 0) {
    satisfactionSection.innerHTML = `
      <p class="satisfaction-meta">Scored cases: N/A</p>
      <p class="satisfaction-meta">Average score: N/A</p>
    `;
  } else {
    const distribution = data.satisfaction_distribution || {};
    const scoredCount = Object.values(distribution).reduce((sum, value) => sum + Number(value), 0);
    const scoreItems = [1, 2, 3, 4, 5]
      .map((score) => {
        const count = distributionCount(distribution, score);
        return `<li>Score ${score} (${SCORE_LABELS[score]}) — ${count}</li>`;
      })
      .join('');

    satisfactionSection.innerHTML = `
      <p class="satisfaction-meta">Scored cases: ${scoredCount} of ${closedTotal}</p>
      <p class="satisfaction-meta">Average score: ${Number(data.average_satisfaction_closed).toFixed(2)} / 5.00</p>
      <ul class="score-list">${scoreItems}</ul>
    `;
  }

  invalidRecordsList.innerHTML = '';
  if (!data.invalid_records.length) {
    const item = document.createElement('li');
    item.textContent = 'No invalid records.';
    invalidRecordsList.appendChild(item);
  } else {
    for (const record of data.invalid_records) {
      const item = document.createElement('li');
      const labels = record.failed_rules.map(ruleLabel).join(', ');
      item.innerHTML = `<strong>${record.incident_id}</strong>: ${labels}`;
      invalidRecordsList.appendChild(item);
    }
  }

  summaryPanel.hidden = false;
  downloadButton.disabled = false;
}

let lastResultId = null;

async function analyzeFile() {
  if (!selectedFile) {
    showError('Please choose a CSV file before analyzing.');
    return;
  }

  clearError();
  setLoading(true);

  const formData = new FormData();
  formData.append('file', selectedFile, selectedFile.name);

  try {
    const response = await fetch('/api/incidents/analyze', {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      showError(renderErrorDetail(payload.detail) || 'Analysis failed. Please try again.');
      return;
    }

    lastResultId = payload.result_id || null;
    renderSummary(payload);
  } catch (_error) {
    showError('Unable to reach the analysis service. Please try again.');
  } finally {
    setLoading(false);
  }
}

async function handleDownload() {
  clearError();

  if (!lastResultId) {
    showError('No analysis available yet. Run an analysis first.');
    return;
  }

  try {
    const response = await fetch(
      `/api/incidents/results/${encodeURIComponent(lastResultId)}/export`,
    );

    if (!response.ok) {
      let message = 'No analysis available yet. Run an analysis first.';
      try {
        const payload = await response.json();
        message = renderErrorDetail(payload.detail) || message;
      } catch {
        // response body not JSON
      }
      showError(message);
      return;
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = 'incident-summary.csv';
    link.click();
    URL.revokeObjectURL(objectUrl);
  } catch {
    showError('Unable to download the export. Please try again.');
  }
}

dropZone.addEventListener('dragover', (event) => {
  event.preventDefault();
  dropZone.classList.add('is-dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('is-dragover');
});

dropZone.addEventListener('drop', (event) => {
  event.preventDefault();
  dropZone.classList.remove('is-dragover');
  const file = event.dataTransfer.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

csvInput.addEventListener('change', () => {
  const file = csvInput.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

analyzeButton.addEventListener('click', analyzeFile);
downloadButton.addEventListener('click', handleDownload);
