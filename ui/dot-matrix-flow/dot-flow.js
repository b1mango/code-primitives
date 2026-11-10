/**
 * Dot Matrix Flow — a dithered dot-matrix particle field painted on <canvas>.
 *
 * The look: a grid of tiny square dots that re-roll on their own beat, so the field shimmers
 * instead of blinking in sync. As a progress fill it dithers in from the left, denser and
 * brighter toward the leading edge, with a few motes spilling ahead of it (the purple
 * "ultracode" shimmer from Claude Code's effort picker).
 *
 * States
 *   idle      faint, sparse motes over the whole box
 *   progress  fill to `progress` (0..1); the shown value eases toward the target
 *   sweep     indeterminate: a comet that sweeps left → right on a loop
 *   pulse     full field with a travelling wave (finishing / "thinking hard" / ultracode on)
 *
 * Zero dependencies. Works as a plain function (`paintFrame`), an imperative controller
 * (`createDotFlow`) or a Web Component (`<dot-flow>`).
 */

const DOT_FLOW_DEFAULTS = Object.freeze({
  pitch: 4, // px between dot origins
  size: 2, // dot side in px
  alpha: 0.8, // global dot opacity
  fps: 30, // the dither reads better (and costs less) at ~30 fps
  ease: 4, // progress easing rate (1/s)
  wash: true, // soft gradient behind the filled part
  color: '#7b4fd8', // fallbacks; CSS vars --dot-flow / --dot-flow-soft win when set
  soft: '#ebe2fb',
});

const DOT_FLOW_STATES = ['idle', 'progress', 'sweep', 'pulse'];

/** Integer hash → [0, 1). Deterministic, so a frame is reproducible from (i, j, t). */
function hash(a, b) {
  let n = (a * 374761393 + b * 668265263) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}

/** Where the fill starts and ends (px) for a state at time t. */
function flowGeometry(state, shown, t, w) {
  if (state === 'sweep') {
    const edge = ((t * 0.45) % 1.25) * w;
    return { start: Math.max(0, edge - w * 0.45), edge };
  }
  if (state === 'progress' || state === 'pulse') {
    return { start: 0, edge: Math.min(1, Math.max(0, shown)) * w };
  }
  return { start: 0, edge: 0 };
}

/** Density (chance a dot is lit) and brightness of the column at x. */
function columnField(x, state, geo, t) {
  let density;
  let bright;
  if (state !== 'idle' && x >= geo.start && x <= geo.edge) {
    const u = (x - geo.start) / Math.max(1, geo.edge - geo.start); // 0 at the tail, 1 at the front
    const ripple = 0.12 * Math.sin(x * 0.045 - t * 4.2);
    density = 0.08 + 0.7 * u ** 2.2 + ripple * u;
    bright = 0.3 + 0.6 * u;
    const near = geo.edge - x;
    if (near < 10) {
      density = Math.max(density, 0.95 - near * 0.03);
      bright = 1;
    }
  } else if (state === 'idle') {
    density = 0.04;
    bright = 0.35;
  } else {
    // outside the fill: sparse, dim motes, a few spilling forward from the front;
    // behind a sweeping comet it stays calm
    const ahead = x - geo.edge;
    density = ahead < 0 ? 0.015 : 0.015 + 0.25 * Math.exp(-ahead / 14);
    bright = 0.35;
  }
  if (state === 'pulse') {
    density = Math.max(density, 0.35 + 0.25 * Math.sin(x * 0.03 - t * 6));
    bright = Math.max(bright, 0.6);
  }
  return { density, bright };
}

/** Parse a canvas-normalised colour (#rrggbb or rgb[a](...)) into a fully transparent rgba. */
function transparentOf(color) {
  const s = String(color).trim();
  let m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(s);
  if (m) return `rgba(${parseInt(m[1], 16)}, ${parseInt(m[2], 16)}, ${parseInt(m[3], 16)}, 0)`;
  m = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i.exec(s);
  if (m) return `rgba(${m[1]}, ${m[2]}, ${m[3]}, 0)`;
  return 'rgba(0, 0, 0, 0)';
}

/**
 * Paint one frame. Pure apart from drawing on `ctx` (already scaled to CSS px).
 * frame: { state, shown, t, color, soft, softClear }
 * Returns the number of dots drawn.
 */
function paintFrame(ctx, w, h, frame, options) {
  const o = options || DOT_FLOW_DEFAULTS;
  const pitch = o.pitch || DOT_FLOW_DEFAULTS.pitch;
  const size = o.size || DOT_FLOW_DEFAULTS.size;
  const alpha = o.alpha == null ? DOT_FLOW_DEFAULTS.alpha : o.alpha;
  const state = frame.state;
  const t = frame.t || 0;
  ctx.clearRect(0, 0, w, h);
  if (!(w > 0 && h > 0)) return 0;

  const geo = flowGeometry(state, frame.shown || 0, t, w);

  if (o.wash !== false && state !== 'idle' && geo.edge > geo.start && frame.soft) {
    const g = ctx.createLinearGradient(geo.start, 0, geo.edge, 0);
    g.addColorStop(0, frame.softClear || transparentOf(frame.soft)); // same hue at alpha 0: no grey ramp
    g.addColorStop(1, frame.soft);
    ctx.globalAlpha = 0.9;
    ctx.fillStyle = g;
    ctx.fillRect(geo.start, 0, geo.edge - geo.start, h);
  }

  ctx.fillStyle = frame.color;
  const rate = state === 'pulse' ? 16 : 9;
  const cols = Math.ceil(w / pitch);
  const rows = Math.max(1, Math.ceil(h / pitch));
  const oy = Math.max(0, (h - (rows - 1) * pitch - size) / 2);
  let drawn = 0;
  for (let i = 0; i < cols; i++) {
    const x = i * pitch;
    const { density, bright } = columnField(x, state, geo, t);
    if (density <= 0) continue;
    for (let j = 0; j < rows; j++) {
      const seed = hash(i, j);
      // each dot re-rolls on its own beat, so the field dithers instead of blinking in sync
      const beat = Math.floor(t * rate * (0.6 + seed) + seed * 7);
      if (hash(i * 7 + beat * 31, j * 13 + beat) > density) continue;
      // fade toward top and bottom so text sits on a calmer band
      const vy = Math.abs(j / Math.max(1, rows - 1) - 0.5) * 2;
      ctx.globalAlpha = bright * (0.35 + 0.65 * seed) * (1 - 0.35 * vy) * alpha;
      ctx.fillRect(x, oy + j * pitch, size, size);
      drawn++;
    }
  }
  ctx.globalAlpha = 1;
  return drawn;
}

function prefersReducedMotion() {
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Drive a canvas: sizing (DPR aware), theming via CSS vars, easing, a capped-fps loop that pauses
 * off-screen, and a static frame under prefers-reduced-motion.
 *
 * options: DOT_FLOW_DEFAULTS + { host, state, progress, reducedMotion, raf, caf }
 *   host      element whose box the field covers (default: canvas.parentElement)
 */
function createDotFlow(canvas, options) {
  const opts = Object.assign({}, DOT_FLOW_DEFAULTS, options);
  const host = opts.host || canvas.parentElement || canvas;
  const ctx = canvas.getContext('2d');
  const raf = opts.raf || (typeof requestAnimationFrame === 'function' ? requestAnimationFrame : (cb) => setTimeout(() => cb(Date.now()), 16));
  const caf = opts.caf || (typeof cancelAnimationFrame === 'function' ? cancelAnimationFrame : clearTimeout);
  const still = opts.reducedMotion == null ? prefersReducedMotion() : !!opts.reducedMotion;

  let state = 'idle';
  let progress = null;
  let shown = 0;
  let t = 0;
  let w = 0;
  let h = 0;
  let color = opts.color;
  let soft = opts.soft;
  let softClear = transparentOf(soft);
  let visible = true;
  let frame = 0;
  let last = 0;
  let acc = 0;
  let destroyed = false;
  const cleanups = [];

  const resolveState = (s, p) => {
    if (s === 'progress' && !(typeof p === 'number' && isFinite(p))) return 'sweep'; // unknown size
    return DOT_FLOW_STATES.includes(s) ? s : 'idle';
  };
  const target = () => (state === 'pulse' ? 1 : state === 'progress' ? Math.min(1, Math.max(0, progress)) : null);

  const recolor = () => {
    const css = typeof getComputedStyle === 'function' ? getComputedStyle(canvas) : null;
    const read = (name) => (css && css.getPropertyValue(name).trim()) || '';
    color = (options && options.color) || read('--dot-flow') || DOT_FLOW_DEFAULTS.color;
    soft = (options && options.soft) || read('--dot-flow-soft') || DOT_FLOW_DEFAULTS.soft;
    ctx.fillStyle = soft;
    softClear = transparentOf(ctx.fillStyle); // canvas normalises any CSS colour
    if (still) paint();
  };

  const resize = () => {
    const dpr = (typeof devicePixelRatio === 'number' && devicePixelRatio) || 1;
    w = host.offsetWidth || 0;
    h = host.offsetHeight || 0;
    if (canvas.style) {
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
    }
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (still) paint();
  };

  function paint() {
    if (destroyed) return 0;
    return paintFrame(ctx, w, h, { state, shown, t, color, soft, softClear }, opts);
  }

  const step = (now) => {
    frame = raf(step);
    const dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
    last = now;
    if (!visible) return;
    t += dt;
    const f = target();
    if (f != null) shown += (f - shown) * (1 - Math.exp(-dt * opts.ease));
    // keep the remainder (minus a little slack for vsync jitter), so 30 fps on a 60 Hz screen is
    // exactly every other frame instead of drifting into 3-frame gaps
    const interval = 1 / opts.fps;
    acc += dt;
    if (acc < interval - 0.002) return;
    acc = Math.min(Math.max(0, acc - interval), interval);
    paint();
  };

  const set = (next) => {
    const n = next || {};
    if ('progress' in n) progress = n.progress;
    const wanted = n.state || (('progress' in n) ? 'progress' : state);
    const prev = state;
    state = resolveState(wanted, progress);
    if (state === 'sweep' && prev !== 'sweep') t = 0; // comet starts from the left
    if (still) {
      const f = target();
      shown = f == null ? 0 : f;
      paint();
    }
  };

  if (typeof ResizeObserver === 'function') {
    const ro = new ResizeObserver(resize);
    ro.observe(host);
    cleanups.push(() => ro.disconnect());
  }
  if (typeof IntersectionObserver === 'function') {
    const io = new IntersectionObserver((entries) => {
      visible = entries[entries.length - 1].isIntersecting;
    });
    io.observe(host);
    cleanups.push(() => io.disconnect());
  }
  if (typeof matchMedia === 'function') {
    const mq = matchMedia('(prefers-color-scheme: dark)');
    if (mq && mq.addEventListener) {
      mq.addEventListener('change', recolor);
      cleanups.push(() => mq.removeEventListener('change', recolor));
    }
  }
  if (typeof MutationObserver === 'function' && typeof document !== 'undefined') {
    // class / data-theme toggles on <html> or <body> usually mean a theme switch
    const mo = new MutationObserver(recolor);
    const attributeFilter = ['class', 'data-theme', 'style'];
    mo.observe(document.documentElement, { attributes: true, attributeFilter });
    if (document.body) mo.observe(document.body, { attributes: true, attributeFilter });
    cleanups.push(() => mo.disconnect());
  }

  set({ state: opts.state || (opts.progress != null ? 'progress' : 'idle'), progress: opts.progress == null ? null : opts.progress });
  shown = target() == null ? 0 : target();
  recolor();
  resize();
  if (!still) frame = raf(step);

  return {
    set,
    resize,
    recolor,
    paint,
    get state() { return state; },
    get shown() { return shown; },
    destroy() {
      destroyed = true;
      caf(frame);
      cleanups.forEach((fn) => fn());
      cleanups.length = 0;
    },
  };
}

/**
 * <dot-flow state="progress" progress="0.4"></dot-flow>
 * Fills its containing block (absolute, inset 0, behind content). Give the parent
 * `position: relative; isolation: isolate` (or the .dot-flow-host class).
 * Attributes: state, progress, pitch, size, alpha, fps, color, soft, host (closest() selector,
 * e.g. host="tr" when mounted inside a table cell to cover the whole row).
 */
const DotFlowElement = typeof HTMLElement === 'undefined' ? null : class DotFlowElement extends HTMLElement {
  static get observedAttributes() {
    return ['state', 'progress'];
  }

  connectedCallback() {
    if (this._flow) return;
    if (!this.shadowRoot) {
      const root = this.attachShadow({ mode: 'open' });
      root.innerHTML = '<style>:host{position:absolute;inset:0;z-index:-1;display:block;pointer-events:none;overflow:visible}canvas{position:absolute;left:0;top:0}</style><canvas></canvas>';
    }
    this.setAttribute('aria-hidden', 'true');
    const sel = this.getAttribute('host');
    const num = (name) => (this.hasAttribute(name) ? Number(this.getAttribute(name)) : undefined);
    const opts = { host: (sel && this.closest(sel)) || this, state: this.getAttribute('state') || undefined, progress: this._progress() };
    for (const k of ['pitch', 'size', 'alpha', 'fps']) if (num(k) != null) opts[k] = num(k);
    for (const k of ['color', 'soft']) if (this.getAttribute(k)) opts[k] = this.getAttribute(k);
    this._flow = createDotFlow(this.shadowRoot.querySelector('canvas'), opts);
  }

  disconnectedCallback() {
    if (this._flow) this._flow.destroy();
    this._flow = null;
  }

  attributeChangedCallback() {
    if (this._flow) this._flow.set({ state: this.getAttribute('state') || undefined, progress: this._progress() });
  }

  _progress() {
    const v = this.getAttribute('progress');
    return v == null || v === '' ? null : Number(v);
  }

  get progress() { return this._progress(); }
  set progress(v) { v == null ? this.removeAttribute('progress') : this.setAttribute('progress', String(v)); }
  get state() { return this.getAttribute('state') || 'idle'; }
  set state(v) { this.setAttribute('state', v); }
};

if (DotFlowElement && typeof customElements !== 'undefined' && !customElements.get('dot-flow')) {
  customElements.define('dot-flow', DotFlowElement);
}

// Export for CommonJS / bundlers / plain <script> tag
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DOT_FLOW_DEFAULTS, DOT_FLOW_STATES, hash, flowGeometry, columnField, transparentOf, paintFrame, createDotFlow, DotFlowElement };
} else if (typeof window !== 'undefined') {
  window.DotFlow = { DOT_FLOW_DEFAULTS, DOT_FLOW_STATES, hash, flowGeometry, columnField, transparentOf, paintFrame, createDotFlow, DotFlowElement };
}
