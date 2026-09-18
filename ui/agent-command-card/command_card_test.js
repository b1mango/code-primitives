const test = require('node:test');
const assert = require('node:assert');

class ClassList {
  constructor() {
    this._set = new Set();
  }
  add(c) { this._set.add(c); }
  remove(c) { this._set.delete(c); }
  contains(c) { return this._set.has(c); }
  has(c) { return this._set.has(c); }
}

class MockElement {
  constructor(tagName = 'div') {
    this.tagName = tagName.toUpperCase();
    this.attributes = new Map();
    this.classList = new ClassList();
    this.children = [];
    this.innerHTML = '';
    this.textContent = '';
    this._listeners = new Map();
  }

  setAttribute(name, val) {
    const old = this.getAttribute(name);
    this.attributes.set(name, String(val));
    if (this.attributeChangedCallback && this.constructor.observedAttributes?.includes(name)) {
      this.attributeChangedCallback(name, old, String(val));
    }
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  removeAttribute(name) {
    const old = this.getAttribute(name);
    this.attributes.delete(name);
    if (this.attributeChangedCallback && this.constructor.observedAttributes?.includes(name)) {
      this.attributeChangedCallback(name, old, null);
    }
  }

  querySelector(selector) {
    return null;
  }

  addEventListener(event, fn) {
    if (!this._listeners.has(event)) this._listeners.set(event, []);
    this._listeners.get(event).push(fn);
  }

  dispatchEvent(event) {
    const list = this._listeners.get(event.type) || [];
    for (const fn of list) fn(event);
  }
}

global.HTMLElement = MockElement;
global.customElements = {
  _registry: new Map(),
  get(name) { return this._registry.get(name); },
  define(name, cls) { this._registry.set(name, cls); }
};
global.CustomEvent = class {
  constructor(type, init = {}) {
    this.type = type;
    this.detail = init.detail;
  }
};

const { AgentCommandCard } = require('./command-card.js');

test('AgentCommandCard - registers custom element', () => {
  assert.strictEqual(typeof AgentCommandCard, 'function');
  assert.strictEqual(global.customElements.get('agent-command-card'), AgentCommandCard);
});

test('AgentCommandCard - renders core structure and attributes', () => {
  const card = new AgentCommandCard();
  card.setAttribute('command', 'npm run build');
  card.setAttribute('status', 'running');
  card.setAttribute('effect', 'pulse');
  card.connectedCallback();

  assert.strictEqual(card.getAttribute('role'), 'region');
  assert.strictEqual(card.getAttribute('data-status'), 'running');
  assert.strictEqual(card.getAttribute('aria-busy'), 'true');
  assert.ok(card.classList.has('effect-pulse'));
});

test('AgentCommandCard - toggles open state', () => {
  const card = new AgentCommandCard();
  card.connectedCallback();

  assert.strictEqual(card.open, false);
  assert.strictEqual(card.getAttribute('data-open'), 'false');

  card.toggle();
  assert.strictEqual(card.open, true);
  assert.strictEqual(card.getAttribute('data-open'), 'true');

  card.toggle();
  assert.strictEqual(card.open, false);
  assert.strictEqual(card.getAttribute('data-open'), 'false');
});

test('AgentCommandCard - status transition from running to success', () => {
  const card = new AgentCommandCard();
  card.connectedCallback();

  card.setAttribute('status', 'running');
  assert.strictEqual(card.getAttribute('data-status'), 'running');
  assert.strictEqual(card.getAttribute('aria-busy'), 'true');

  card.setAttribute('status', 'success');
  assert.strictEqual(card.getAttribute('data-status'), 'success');
  assert.strictEqual(card.getAttribute('aria-busy'), null);
});
