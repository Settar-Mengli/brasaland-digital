/**
 * Brasa Points registration form behavior.
 *
 * Responsibilities:
 *   1. Populate dependent dropdowns: Country → City → Favorite location.
 *   2. Validate all 11 form fields against the Brasa Points program rules.
 *   3. Reveal the success message on a valid submit; surface inline errors otherwise.
 *
 * No external dependencies. Single IIFE; no globals.
 */

(function () {
  'use strict';

  // ── CONSTANTS ──────────────────────────────────────────────────────────────────────────────────

  const LOCATION_DATA = Object.freeze({
    CO: Object.freeze({
      Medellín: Object.freeze([
        'Brasaland El Poblado',
        'Brasaland Laureles',
        'Brasaland Envigado',
        'Brasaland Sabaneta',
      ]),
      Bogotá: Object.freeze(['Brasaland Usaquén', 'Brasaland Chapinero', 'Brasaland Zona Rosa']),
      Cali: Object.freeze(['Brasaland Granada', 'Brasaland Ciudad Jardín', 'Brasaland Unicentro']),
    }),
    US: Object.freeze({
      Miami: Object.freeze(['Brasaland Brickell', 'Brasaland Coral Gables']),
      Orlando: Object.freeze(['Brasaland Downtown', 'Brasaland International Drive']),
    }),
  });

  const ERROR_MESSAGES = Object.freeze({
    fullName: 'Enter your full name (first and last name)',
    email: 'Enter a valid email (example: name@email.com)',
    phone: 'Phone must include country code (example: +57 300 123 4567 or +1 305 123 4567)',
    country: 'Select your country',
    city: 'Select your city',
    dateOfBirth: 'You must be 18 or older to register for Brasa Points',
    referral: 'Tell us how you found Brasaland',
    terms: 'You must accept the Brasa Points program terms to continue',
  });

  // ── DOM HELPERS ────────────────────────────────────────────────────────────────────────────────

  /**
   * Get an element by ID; throws if missing.
   * @param {string} id
   * @returns {HTMLElement}
   */
  function getEl(id) {
    const el = document.getElementById(id);
    if (!el) throw new Error(`Required element #${id} not found`);
    return el;
  }

  /**
   * Show an error message for a field; sets aria-invalid on the input.
   * @param {string} fieldId - the input id (NOT the error span id)
   * @param {string} message
   */
  function showError(fieldId, message) {
    const input = getEl(fieldId);
    const errorEl = getEl(`${fieldId}-error`);
    input.setAttribute('aria-invalid', 'true');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
  }

  /**
   * Clear the error for a field.
   * @param {string} fieldId
   */
  function clearError(fieldId) {
    const input = document.getElementById(fieldId);
    const errorEl = document.getElementById(`${fieldId}-error`);
    if (input) input.removeAttribute('aria-invalid');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.add('hidden');
    }
  }

  /** Clear all known field errors. */
  function clearAllErrors() {
    clearError('full-name');
    clearError('email');
    clearError('phone');
    clearError('date-of-birth');
    clearError('country');
    clearError('city');
    clearError('referral');
    clearError('terms');
  }

  // ── VALIDATORS ────────────────────────────────────────────────────────────────────────────────

  /**
   * Validate the full name field.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validateFullName(value) {
    const trimmed = value.trim();
    if (!trimmed) return ERROR_MESSAGES.fullName;
    const words = trimmed.split(/\s+/).filter(Boolean);
    if (words.length < 2) return ERROR_MESSAGES.fullName;
    return null;
  }

  /**
   * Validate the email field.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validateEmail(value) {
    const trimmed = value.trim();
    if (!trimmed) return ERROR_MESSAGES.email;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return ERROR_MESSAGES.email;
    return null;
  }

  /**
   * Validate the phone field. Must start with +57 or +1.
   * After stripping non-digits: +57 requires 12 digits total, +1 requires 11.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validatePhone(value) {
    const trimmed = value.trim();
    if (!trimmed) return ERROR_MESSAGES.phone;

    const isColombia = trimmed.startsWith('+57');
    const isUS = trimmed.startsWith('+1');

    if (!isColombia && !isUS) return ERROR_MESSAGES.phone;

    const digits = trimmed.replace(/\D/g, '');
    if (isColombia && digits.length !== 12) return ERROR_MESSAGES.phone;
    if (isUS && digits.length !== 11) return ERROR_MESSAGES.phone;

    return null;
  }

  /**
   * Validate the date of birth field. User must be 18 or older.
   * @param {string} value - date string in YYYY-MM-DD format
   * @returns {string|null} Error message or null if valid.
   */
  function validateDateOfBirth(value) {
    if (!value) return ERROR_MESSAGES.dateOfBirth;
    const dob = new Date(value);
    const now = new Date();
    const eighteenYearsAgo = new Date(now.getFullYear() - 18, now.getMonth(), now.getDate());
    if (dob > eighteenYearsAgo) return ERROR_MESSAGES.dateOfBirth;
    return null;
  }

  /**
   * Validate the country field.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validateCountry(value) {
    if (value !== 'CO' && value !== 'US') return ERROR_MESSAGES.country;
    return null;
  }

  /**
   * Validate the city field.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validateCity(value) {
    if (!value.trim()) return ERROR_MESSAGES.city;
    return null;
  }

  /**
   * Validate the referral field.
   * @param {string} value
   * @returns {string|null} Error message or null if valid.
   */
  function validateReferral(value) {
    if (!value) return ERROR_MESSAGES.referral;
    return null;
  }

  /**
   * Validate the terms checkbox.
   * @param {boolean} checked
   * @returns {string|null} Error message or null if valid.
   */
  function validateTerms(checked) {
    if (!checked) return ERROR_MESSAGES.terms;
    return null;
  }

  // ── DEPENDENT DROPDOWNS ───────────────────────────────────────────────────────────────────────

  /**
   * Populate a select element with a placeholder and a list of items.
   * Uses DOM API only — no innerHTML.
   * @param {HTMLSelectElement} selectEl
   * @param {string[]} items - option text values (also used as option values)
   * @param {string} placeholderText - text for the disabled placeholder option
   */
  function populateSelect(selectEl, items, placeholderText) {
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.disabled = true;
    placeholder.selected = true;
    placeholder.textContent = placeholderText;

    const options = [placeholder];
    items.forEach(function (item) {
      const option = document.createElement('option');
      option.value = item;
      option.textContent = item;
      options.push(option);
    });

    selectEl.replaceChildren(...options);
  }

  /** Handle country select change: populate cities, reset favorite location. */
  function onCountryChange() {
    const country = getEl('country').value;
    const cityEl = getEl('city');
    const favEl = getEl('favorite-location');

    // Always reset favorite location first
    populateSelect(favEl, [], 'Select your city first');
    favEl.disabled = true;

    if (country === 'CO' || country === 'US') {
      const cities = Object.keys(LOCATION_DATA[country]);
      populateSelect(cityEl, cities, 'Select your city');
      cityEl.disabled = false;
    } else {
      populateSelect(cityEl, [], 'Select your country first');
      cityEl.disabled = true;
    }
  }

  /** Handle city select change: populate favorite locations. */
  function onCityChange() {
    const country = getEl('country').value;
    const city = getEl('city').value;
    const favEl = getEl('favorite-location');

    if (country && city && LOCATION_DATA[country] && LOCATION_DATA[country][city]) {
      const locations = LOCATION_DATA[country][city];
      populateSelect(favEl, locations, 'Select a location (optional)');
      favEl.disabled = false;
    } else {
      populateSelect(favEl, [], 'Select your city first');
      favEl.disabled = true;
    }
  }

  // ── FORM HANDLERS ─────────────────────────────────────────────────────────────────────────────

  /**
   * Validate the entire form. Returns errors in DOM order.
   * @returns {Array<{fieldId: string, message: string}>}
   */
  function validateForm() {
    const errors = [];

    const fullNameErr = validateFullName(getEl('full-name').value);
    if (fullNameErr) errors.push({ fieldId: 'full-name', message: fullNameErr });

    const emailErr = validateEmail(getEl('email').value);
    if (emailErr) errors.push({ fieldId: 'email', message: emailErr });

    const phoneErr = validatePhone(getEl('phone').value);
    if (phoneErr) errors.push({ fieldId: 'phone', message: phoneErr });

    const dobErr = validateDateOfBirth(getEl('date-of-birth').value);
    if (dobErr) errors.push({ fieldId: 'date-of-birth', message: dobErr });

    const countryErr = validateCountry(getEl('country').value);
    if (countryErr) errors.push({ fieldId: 'country', message: countryErr });

    const cityErr = validateCity(getEl('city').value);
    if (cityErr) errors.push({ fieldId: 'city', message: cityErr });

    const referralErr = validateReferral(getEl('referral').value);
    if (referralErr) errors.push({ fieldId: 'referral', message: referralErr });

    const termsErr = validateTerms(getEl('terms').checked);
    if (termsErr) errors.push({ fieldId: 'terms', message: termsErr });

    return errors;
  }

  /**
   * Submit handler — preventDefault, validate, show errors or reveal success.
   * @param {SubmitEvent} event
   */
  function onSubmit(event) {
    event.preventDefault();
    clearAllErrors();
    getEl('success-message').classList.add('hidden');

    const errors = validateForm();

    if (errors.length > 0) {
      errors.forEach(function ({ fieldId, message }) {
        showError(fieldId, message);
      });
      const firstField = document.getElementById(errors[0].fieldId);
      if (firstField) firstField.focus();
      return;
    }

    const successEl = getEl('success-message');
    successEl.classList.remove('hidden');
    successEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /**
   * Reset handler — clear errors and reset dependent selects after native reset completes.
   */
  function onReset() {
    setTimeout(function () {
      clearAllErrors();

      const city = getEl('city');
      city.disabled = true;
      const cityPlaceholder = document.createElement('option');
      cityPlaceholder.value = '';
      cityPlaceholder.textContent = 'Select your country first';
      city.replaceChildren(cityPlaceholder);

      const fav = getEl('favorite-location');
      fav.disabled = true;
      const favPlaceholder = document.createElement('option');
      favPlaceholder.value = '';
      favPlaceholder.textContent = 'Select your city first';
      fav.replaceChildren(favPlaceholder);

      getEl('success-message').classList.add('hidden');
    }, 0);
  }

  // ── INIT ──────────────────────────────────────────────────────────────────────────────────────

  /** Wire up all event listeners. */
  function init() {
    const form = getEl('brasa-points-form');
    form.addEventListener('submit', onSubmit);
    form.addEventListener('reset', onReset);
    getEl('country').addEventListener('change', onCountryChange);
    getEl('city').addEventListener('change', onCityChange);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
