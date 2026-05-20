/**
 * Mobile navigation toggle.
 *
 * Wires up the hamburger button to show/hide the stacked mobile nav panel.
 * Maintains aria-expanded on the button and the hidden attribute on the panel.
 * Handles Escape-to-close with focus restoration.
 *
 * No external dependencies. Single IIFE; no globals.
 */

(function () {
  'use strict';

  let toggle = null;
  let panel = null;

  // ── HELPERS ───────────────────────────────────────────────────────────────────────────────────

  /** Open the mobile nav panel. */
  function openPanel() {
    panel.removeAttribute('hidden');
    toggle.setAttribute('aria-expanded', 'true');
  }

  /**
   * Close the mobile nav panel and return focus to the toggle button.
   */
  function closePanel() {
    panel.setAttribute('hidden', '');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  }

  // ── HANDLERS ──────────────────────────────────────────────────────────────────────────────────

  /** Handle toggle button click. */
  function onToggleClick() {
    if (panel.hasAttribute('hidden')) {
      openPanel();
    } else {
      closePanel();
    }
  }

  /**
   * Handle keydown events — Escape closes the panel when focus is inside it or on the button.
   * @param {KeyboardEvent} event
   */
  function onKeyDown(event) {
    if (event.key !== 'Escape') return;
    if (panel.hasAttribute('hidden')) return;
    const focusInPanel = panel.contains(document.activeElement);
    const focusOnToggle = document.activeElement === toggle;
    if (focusInPanel || focusOnToggle) {
      event.preventDefault();
      closePanel();
    }
  }

  /**
   * Handle click on a nav link inside the panel — close the panel.
   */
  function onLinkClick() {
    closePanel();
  }

  // ── INIT ──────────────────────────────────────────────────────────────────────────────────────

  /**
   * Wire up all event listeners.
   * No-op if either required element is missing.
   */
  function init() {
    toggle = document.getElementById('mobile-nav-toggle');
    panel = document.getElementById('mobile-nav-panel');
    if (!toggle || !panel) return;

    toggle.addEventListener('click', onToggleClick);
    document.addEventListener('keydown', onKeyDown);

    panel.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', onLinkClick);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
