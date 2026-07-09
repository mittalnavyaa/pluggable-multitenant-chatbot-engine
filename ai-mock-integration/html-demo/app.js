/**
 * ai-mock-integration/html-demo/app.js
 *
 * Host-page JavaScript for the Envoy Chatbot integration demo.
 *
 * This file demonstrates two things:
 *   1. How to call the widget's JavaScript public API from host-page code.
 *   2. How to listen for custom events fired by the widget.
 *
 * In a real integration, you would call these methods from your own
 * application logic — for example:
 *   - Call widget.open() when a user clicks your "Help" button
 *   - Call widget.sendMessage() to pre-fill a support topic
 *   - Listen to envoy-message-received to log analytics events
 */

// ─── Step 1: Get a reference to the widget element ───────────────────────────
//
// The widget is a standard HTML element. You access it the same way you
// would access any other element — by ID, class, or querySelector.
//
const widget = document.getElementById('envoy-widget');

// ─── Step 2: Expose the widget API to the control panel buttons ───────────────
//
// We attach the widget reference to a named object so the onclick handlers
// in index.html can call it cleanly. In a real app you would import or
// reference the widget however fits your architecture.
//
window.widgetAPI = widget;

// ─── Step 3: Set up the event log display ────────────────────────────────────
//
// The widget fires four custom events. We listen for all of them and
// display them in the on-screen event log panel.
//
const eventLogEl = document.getElementById('event-log');

/**
 * Appends a new entry to the on-screen event log.
 * @param {string} eventName - The name of the custom event.
 * @param {any} detail - The event detail payload (optional).
 */
function logEvent(eventName, detail) {
  // Remove the placeholder text on first event
  const placeholder = eventLogEl.querySelector('.event-log-placeholder');
  if (placeholder) {
    placeholder.remove();
  }

  const time = new Date().toLocaleTimeString();
  const entry = document.createElement('div');
  entry.className = 'event-entry';

  const detailText = detail ? ` — ${JSON.stringify(detail)}` : '';
  entry.textContent = `[${time}]  ${eventName}${detailText}`;

  eventLogEl.appendChild(entry);

  // Auto-scroll to the latest entry
  eventLogEl.scrollTop = eventLogEl.scrollHeight;

  // Also log to the browser console for developer inspection
  console.log(`[envoy-event] ${eventName}`, detail || '');
}

// ─── Step 4: Register custom event listeners ─────────────────────────────────
//
// The widget dispatches these four custom events. All events bubble and
// are composed (they cross Shadow DOM boundaries), so you can listen on
// the element itself or on any ancestor including document.
//

/**
 * Fired when the chat window opens.
 * Use this to: pause background animations, log analytics, etc.
 */
widget.addEventListener('envoy-chat-opened', () => {
  logEvent('envoy-chat-opened');
});

/**
 * Fired when the chat window closes.
 * Use this to: resume background animations, save state, etc.
 */
widget.addEventListener('envoy-chat-closed', () => {
  logEvent('envoy-chat-closed');
});

/**
 * Fired when the user sends a message.
 * event.detail = { text: string }
 * Use this to: log the user's query to your analytics system.
 */
widget.addEventListener('envoy-message-sent', (event) => {
  logEvent('envoy-message-sent', event.detail);
});

/**
 * Fired when the bot finishes responding.
 * event.detail = { text: string }
 * Use this to: log the bot's response, trigger follow-up actions, etc.
 */
widget.addEventListener('envoy-message-received', (event) => {
  logEvent('envoy-message-received', event.detail);
});

// ─── Step 5: Utility functions ───────────────────────────────────────────────

/**
 * Clears the on-screen event log.
 * Called by the "Clear Log" button in the control panel.
 */
window.clearEventLog = function () {
  eventLogEl.innerHTML = '<div class="event-log-placeholder">Log cleared. Waiting for events...</div>';
};

// ─── Step 6: Log initialization ──────────────────────────────────────────────
//
// Confirm in the console that the host page script loaded successfully
// and the widget element was found.
//
console.log('[envoy-demo] Host page script loaded.');
console.log('[envoy-demo] Widget element:', widget);
console.log('[envoy-demo] Widget public API methods available:', [
  'open()',
  'close()',
  'toggle()',
  'sendMessage(text)',
  'resetConversation()',
  'destroy()',
]);
