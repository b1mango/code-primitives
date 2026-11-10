const test = require('node:test');
const assert = require('node:assert');

const {
  DOT_FLOW_DEFAULTS,
  hash,
  flowGeometry,
  columnField,
  transparentOf,
  paintFrame,
  createDotFlow,
} = require('./dot-flow.js');

/** Minimal 2D context that records what was drawn. */
function mockCtx() {
  return {
    dots: [],
    rects: 0,
    gradients: 0,
    cleared: 0,
    globalAlpha: 1,
    _fill: '#000000',
    set fillStyle(v) {
      // mimic canvas normalisation of plain hex
      this._fill = typeof v === 'string' && /^#[0-9a-f]{3}$/i.test(v)
        ? '#' + v.slice(1).split('').map((c) => c + c).join('').toLowerCase()
        : v;
    },
    get fillStyle() { return this._fill; },
    clearRect() { this.cleared++; this.dots = []; },
    setTransform() {},
    createLinearGradient() {
      this.gradients++;
      return { stops: [], addColorStop(o, c) { this.stops.push([o, c]); } };
    },
    fillRect(x, y, w, h) {
      this.rects++;
      if (typeof this._fill === 'string') this.dots.push({ x, y, w, h, a: this.globalAlpha });
    },
  };
}

const frame = (state, shown, t = 1.3) => ({ state, shown, t, color: '#7b4fd8', soft: '#ebe2fb' });

test('hash is deterministic and lands in [0, 1)', () => {
  let sum = 0;
  const N = 20000;
  for (let i = 0; i < N; i++) {
    const v = hash(i, i * 3 + 1);
    assert.ok(v >= 0 && v < 1, `out of range: ${v}`);
    assert.strictEqual(v, hash(i, i * 3 + 1));
    sum += v;
  }
  const mean = sum / N;
  assert.ok(Math.abs(mean - 0.5) < 0.02, `poorly distributed, mean ${mean}`);
});

test('geometry: progress fills from 0 to fraction, clamped', () => {
  assert.deepStrictEqual(flowGeometry('progress', 0.5, 0, 200), { start: 0, edge: 100 });
  assert.deepStrictEqual(flowGeometry('progress', 1.7, 0, 200), { start: 0, edge: 200 });
  assert.deepStrictEqual(flowGeometry('progress', -1, 0, 200), { start: 0, edge: 0 });
  assert.deepStrictEqual(flowGeometry('idle', 0.5, 0, 200), { start: 0, edge: 0 });
});

test('geometry: sweep is a moving comet with a bounded tail', () => {
  const w = 400;
  let prev = -1;
  for (let t = 0; t < 2.7; t += 0.25) {
    const g = flowGeometry('sweep', 0, t, w);
    assert.ok(g.edge - g.start <= w * 0.45 + 1e-9);
    assert.ok(g.start >= 0);
    if (t > 0) assert.ok(g.edge > prev, 'comet should advance within one loop');
    prev = g.edge;
  }
  // loops after 1.25 widths
  assert.ok(flowGeometry('sweep', 0, 1.25 / 0.45 + 0.01, w).edge < 10);
});

test('field: denser and brighter toward the leading edge, sparse beyond it', () => {
  const geo = { start: 0, edge: 300 };
  const tail = columnField(20, 'progress', geo, 0);
  const mid = columnField(200, 'progress', geo, 0);
  const front = columnField(298, 'progress', geo, 0);
  const ahead = columnField(330, 'progress', geo, 0);
  const far = columnField(600, 'progress', geo, 0);
  assert.ok(tail.density < mid.density && mid.density < front.density);
  assert.ok(tail.bright < front.bright);
  assert.strictEqual(front.bright, 1);
  assert.ok(ahead.density > far.density, 'motes spill forward then thin out');
  assert.ok(far.density < 0.02);
});

test('field: pulse keeps a density floor everywhere', () => {
  const geo = { start: 0, edge: 0 };
  for (let x = 0; x < 800; x += 13) {
    const f = columnField(x, 'pulse', geo, 0.7);
    assert.ok(f.density >= 0.1 - 1e-9 && f.bright >= 0.6);
  }
});

test('transparentOf keeps the hue at alpha 0', () => {
  assert.strictEqual(transparentOf('#ebe2fb'), 'rgba(235, 226, 251, 0)');
  assert.strictEqual(transparentOf('rgba(38, 29, 61, 0.5)'), 'rgba(38, 29, 61, 0)');
  assert.strictEqual(transparentOf('rgb(1 2 3)'), 'rgba(1, 2, 3, 0)');
  assert.strictEqual(transparentOf('nonsense'), 'rgba(0, 0, 0, 0)');
});

test('paintFrame: more progress lights more dots; all dots on the pitch grid', () => {
  const W = 480;
  const H = 36;
  const counts = [0, 0.25, 0.5, 1].map((p) => {
    const ctx = mockCtx();
    const n = paintFrame(ctx, W, H, frame('progress', p), DOT_FLOW_DEFAULTS);
    for (const d of ctx.dots) {
      assert.strictEqual(d.x % DOT_FLOW_DEFAULTS.pitch, 0);
      assert.strictEqual(d.w, DOT_FLOW_DEFAULTS.size);
      assert.ok(d.a > 0 && d.a <= DOT_FLOW_DEFAULTS.alpha + 1e-9);
      assert.ok(d.y >= 0 && d.y + d.h <= H);
    }
    return n;
  });
  for (let i = 1; i < counts.length; i++) assert.ok(counts[i] > counts[i - 1], `counts ${counts}`);
});

test('paintFrame: dots cluster before the edge', () => {
  const ctx = mockCtx();
  paintFrame(ctx, 400, 32, frame('progress', 0.5), DOT_FLOW_DEFAULTS);
  const before = ctx.dots.filter((d) => d.x <= 200).length;
  const after = ctx.dots.filter((d) => d.x > 200).length;
  assert.ok(before > after * 3, `before ${before}, after ${after}`);
});

test('paintFrame: same input → same frame; time moves the dither', () => {
  const a = mockCtx();
  const b = mockCtx();
  const c = mockCtx();
  paintFrame(a, 300, 24, frame('progress', 0.6, 2), DOT_FLOW_DEFAULTS);
  paintFrame(b, 300, 24, frame('progress', 0.6, 2), DOT_FLOW_DEFAULTS);
  paintFrame(c, 300, 24, frame('progress', 0.6, 2.5), DOT_FLOW_DEFAULTS);
  assert.deepStrictEqual(a.dots, b.dots);
  assert.notDeepStrictEqual(a.dots, c.dots);
});

test('paintFrame: idle is faint, no wash; zero size draws nothing', () => {
  const ctx = mockCtx();
  const n = paintFrame(ctx, 400, 32, frame('idle', 0), DOT_FLOW_DEFAULTS);
  const total = Math.ceil(400 / 4) * Math.ceil(32 / 4);
  assert.ok(n < total * 0.1);
  assert.strictEqual(ctx.gradients, 0);
  assert.strictEqual(paintFrame(mockCtx(), 0, 32, frame('progress', 1), DOT_FLOW_DEFAULTS), 0);
});

test('paintFrame: wash option toggles the gradient', () => {
  const on = mockCtx();
  const off = mockCtx();
  paintFrame(on, 200, 20, frame('progress', 0.5), DOT_FLOW_DEFAULTS);
  paintFrame(off, 200, 20, frame('progress', 0.5), { ...DOT_FLOW_DEFAULTS, wash: false });
  assert.strictEqual(on.gradients, 1);
  assert.strictEqual(off.gradients, 0);
});

function mockCanvas(hostW = 320, hostH = 30) {
  const ctx = mockCtx();
  const host = { offsetWidth: hostW, offsetHeight: hostH };
  return { ctx, host, canvas: { style: {}, width: 0, height: 0, parentElement: host, getContext: () => ctx } };
}

test('controller (reduced motion): sizes to host, paints on every set, resolves states', () => {
  const { ctx, host, canvas } = mockCanvas();
  const flow = createDotFlow(canvas, { reducedMotion: true, raf: () => assert.fail('no loop under reduced motion') });
  assert.strictEqual(canvas.style.width, '320px');
  assert.strictEqual(canvas.width, 320);
  assert.strictEqual(flow.state, 'idle');

  const before = ctx.cleared;
  flow.set({ progress: 0.4 });
  assert.strictEqual(flow.state, 'progress');
  assert.strictEqual(flow.shown, 0.4, 'reduced motion jumps straight to the target');
  assert.ok(ctx.cleared > before);

  flow.set({ progress: null });
  assert.strictEqual(flow.state, 'sweep', 'unknown size falls back to the sweep');
  flow.set({ state: 'pulse' });
  assert.strictEqual(flow.state, 'pulse');
  assert.strictEqual(flow.shown, 1);
  flow.set({ state: 'bogus' });
  assert.strictEqual(flow.state, 'idle');

  host.offsetWidth = 100;
  flow.resize();
  assert.strictEqual(canvas.style.width, '100px');
  flow.destroy();
  const after = ctx.cleared;
  flow.paint();
  assert.strictEqual(ctx.cleared, after, 'no painting after destroy');
});

test('controller (animated): eases toward target, caps fps, cancels on destroy', () => {
  const { ctx, canvas } = mockCanvas();
  const queue = [];
  let cancelled = null;
  const flow = createDotFlow(canvas, {
    reducedMotion: false,
    progress: 0,
    raf: (cb) => { queue.push(cb); return queue.length; },
    caf: (id) => { cancelled = id; },
  });
  flow.set({ progress: 1 });
  let now = 1000;
  let paints = 0;
  for (let i = 0; i < 120; i++) { // 2 s at 60 Hz
    const before = ctx.cleared;
    queue.shift()(now);
    now += 1000 / 60;
    if (ctx.cleared > before) paints++;
  }
  assert.ok(flow.shown > 0.95 && flow.shown <= 1, `shown ${flow.shown}`);
  assert.ok(paints >= 55 && paints <= 62, `~30 fps expected, got ${paints} paints in 2 s`);
  flow.destroy();
  assert.ok(cancelled != null);
});

test('benchmark: one 720×40 frame', () => {
  const ctx = mockCtx();
  const N = 300;
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < N; i++) paintFrame(ctx, 720, 40, frame('progress', 0.7, i / 30), DOT_FLOW_DEFAULTS);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6 / N;
  console.log(`  paintFrame 720x40: ${ms.toFixed(3)} ms/frame (mock ctx)`);
  assert.ok(ms < 8, `too slow: ${ms} ms/frame`);
});
