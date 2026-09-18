/**
 * AgentCommandCard Web Component & Vanilla Factory
 * Zero-dependency, lightweight, keyboard accessible.
 */

class AgentCommandCard extends HTMLElement {
  static get observedAttributes() {
    return ['command', 'status', 'effect', 'duration', 'open'];
  }

  constructor() {
    super();
    this._isOpen = false;
    this._status = 'idle';
    this._effect = 'native';
  }

  connectedCallback() {
    this.classList.add('agent-command-card');
    this.setAttribute('role', 'region');
    this.setAttribute('aria-label', `Command: ${this.getAttribute('command') || 'terminal execution'}`);
    this.render();
    this.bindEvents();
    this.updateState();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    if (name === 'open') {
      this._isOpen = newValue !== null && newValue !== 'false';
    } else if (name === 'status') {
      this._status = newValue || 'idle';
    } else if (name === 'effect') {
      this._effect = newValue || 'native';
    }
    this.updateState();
  }

  get open() {
    return this._isOpen;
  }

  set open(val) {
    if (val) {
      this.setAttribute('open', '');
    } else {
      this.removeAttribute('open');
    }
  }

  get status() {
    return this._status;
  }

  set status(val) {
    this.setAttribute('status', val);
  }

  render() {
    const cmd = this.getAttribute('command') || '';
    const bodyContent = this.innerHTML.trim();

    this.innerHTML = `
      <div class="acc-header" role="button" tabindex="0" aria-expanded="false">
        <svg class="acc-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round">
          <path d="M6 8l4 4-4 4"></path>
          <path d="M12 16h6"></path>
        </svg>
        <div class="acc-cmd">
          <span class="acc-cmd-text">${this.escapeHtml(cmd)}</span>
          <span class="acc-cursor"></span>
        </div>
        <div class="acc-meta">
          <span class="acc-duration"></span>
          <span class="acc-spinner-slot"></span>
        </div>
        <svg class="acc-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round">
          <polyline points="9 6 15 12 9 18"></polyline>
        </svg>
      </div>
      <div class="acc-body" role="log" aria-live="polite">${bodyContent}</div>
    `;
  }

  bindEvents() {
    const header = this.querySelector('.acc-header');
    if (!header) return;

    header.addEventListener('click', () => this.toggle());
    header.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggle();
      }
    });
  }

  toggle() {
    this.open = !this.open;
    this.dispatchEvent(new CustomEvent('toggle', { detail: { open: this.open }, bubbles: true }));
  }

  updateState() {
    const header = this.querySelector('.acc-header');
    const spinnerSlot = this.querySelector('.acc-spinner-slot');
    const durationEl = this.querySelector('.acc-duration');
    const cmdTextEl = this.querySelector('.acc-cmd-text');

    if (cmdTextEl && this.getAttribute('command')) {
      cmdTextEl.textContent = this.getAttribute('command');
    }

    // Update open state
    this.setAttribute('data-open', this._isOpen ? 'true' : 'false');
    if (header) {
      header.setAttribute('aria-expanded', this._isOpen ? 'true' : 'false');
    }

    // Update status
    this.setAttribute('data-status', this._status);
    if (this._status === 'running') {
      this.setAttribute('aria-busy', 'true');
      if (spinnerSlot) {
        spinnerSlot.innerHTML = '<div class="acc-spinner-ring"></div>';
      }
    } else {
      this.removeAttribute('aria-busy');
      if (spinnerSlot) {
        spinnerSlot.innerHTML = '';
      }
    }

    // Update effect classes
    this.classList.remove('effect-pulse', 'effect-shimmer', 'effect-beam', 'effect-cursor');
    if (this._effect && this._effect !== 'native') {
      this.classList.add(`effect-${this._effect}`);
    }

    // Update duration
    const dur = this.getAttribute('duration');
    if (durationEl) {
      durationEl.textContent = dur || '';
    }
  }

  appendOutput(text) {
    const body = this.querySelector('.acc-body');
    if (body) {
      body.textContent += text;
      body.scrollTop = body.scrollHeight;
    }
  }

  setOutput(text) {
    const body = this.querySelector('.acc-body');
    if (body) {
      body.textContent = text;
    }
  }

  escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

if (typeof customElements !== 'undefined' && !customElements.get('agent-command-card')) {
  customElements.define('agent-command-card', AgentCommandCard);
}

// Export for ES modules / CommonJS / Browser script tag
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AgentCommandCard };
}
