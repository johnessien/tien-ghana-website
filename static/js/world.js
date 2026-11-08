/* TIEN Ghana: immersive front-end (Three.js r128 + GSAP ScrollTrigger).
   Server-rendered Django pages; this script only enhances them. <body data-page> picks the 3D state. */
(() => {
'use strict';
window.__tienReady = true;
const docEl = document.documentElement;
try {
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const mobile = matchMedia('(max-width: 860px)').matches;
// low-power: phones, fewer than 4 CPU cores, under 4 GB memory, or Data Saver on
const lowPower = mobile || (navigator.hardwareConcurrency || 8) < 4 || (navigator.deviceMemory || 8) < 4 ||
  !!(navigator.connection && navigator.connection.saveData);
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const G = typeof gsap !== 'undefined', ST = G && typeof ScrollTrigger !== 'undefined';
if (ST) gsap.registerPlugin(ScrollTrigger);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const page = document.body.dataset.page || 'home';
let homeTriggers = [];

/* ================= DATA (from Django via json_script) ================= */
const DATA = JSON.parse(($('#world-data') || { textContent: '{}' }).textContent || '{}');
const P = (lat, lon) => [(lon + 3.26) / 4.46 * 300, (11.17 - lat) / 6.43 * 440];
const CAMPUSES = (DATA.campuses || []).map(c => ({ ...c, xy: P(c.lat, c.lon) }));
const WAVES = DATA.waves || [0, 0, 0, 0];
const idxOf = id => CAMPUSES.findIndex(c => String(c.id) === String(id));

/* headline split (words stay readable without JS; this only wraps them for the rise animation) */
$$('.split').forEach(h => {
  const walk = n => [...n.childNodes].map(ch => ch.nodeType === 3 ? esc(ch.textContent).split(/(\s+)/).map(w => /^\s+$/.test(w) || !w ? w : `<span class="w"><span>${w}</span></span>`).join('') : `<span class="${ch.className}">${walk(ch)}</span>`).join('');
  h.innerHTML = walk(h);
});

/* ================= 3D WORLD ================= */
const World = (() => {
  const canvas = $('#gl');
  const ok = typeof THREE !== 'undefined' && (() => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl') || c.getContext('experimental-webgl')); } catch (e) { return false; } })();
  const api = { ok, set() {}, params: {}, onPick: null, morphTo() {}, u: { uDim: { value: 0 }, uCut: { value: 0 }, uRise: { value: 1 }, uGauge: { value: 0 } } };
  if (!ok) { canvas.style.display = 'none'; return api; }
  $('#fallbackBg').style.display = 'none';

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !mobile, alpha: false, powerPreference: 'high-performance' });
  const PR = Math.min(devicePixelRatio, mobile ? 1.5 : 2);
  renderer.setPixelRatio(PR); renderer.setClearColor(0x000E45, 1);
  const scene = new THREE.Scene(); scene.fog = new THREE.Fog(0x000E45, 18, 42);
  const camera = new THREE.PerspectiveCamera(36, innerWidth / innerHeight, .1, 100);
  scene.add(new THREE.AmbientLight(0xffffff, .5));
  const key = new THREE.DirectionalLight(0xffffff, .9); key.position.set(-4, -6, 10); scene.add(key);
  const rimL = new THREE.DirectionalLight(0xFEB800, .4); rimL.position.set(6, 6, 4); scene.add(rimL);
  const root = new THREE.Group(); scene.add(root);

  /* ---- particle states ---- */
  const N = mobile ? 3600 : 7000;
  const S = .022, toW = (x, y) => [(x - 150) * S, -(y - 220) * S];
  const PATH = 'M81.5 440.0 L78.1 440.0 L72.7 434.1 L60.0 425.8 L12.7 415.3 L13.0 413.6 L18.4 413.1 L23.2 410.6 L28.4 406.0 L31.3 400.6 L32.3 394.2 L31.3 388.4 L28.4 383.0 L19.3 376.4 L14.7 370.7 L13.7 360.0 L9.8 350.2 L8.8 342.8 L3.4 332.1 L0.0 318.4 L0.0 298.8 L16.6 271.4 L21.0 244.0 L23.5 238.1 L32.3 222.4 L40.6 213.1 L48.0 199.4 L48.9 193.6 L44.0 163.7 L39.2 152.5 L31.3 144.1 L35.7 132.9 L36.7 121.6 L29.9 99.6 L32.8 93.2 L32.8 84.4 L29.9 76.6 L29.4 65.8 L26.4 59.5 L25.5 50.2 L20.6 40.4 L20.6 33.0 L26.9 18.8 L27.4 14.4 L30.1 12.2 L37.0 12.7 L47.7 16.2 L56.5 13.7 L106.0 13.7 L114.3 11.7 L129.5 13.7 L148.1 12.2 L157.8 14.2 L166.7 12.7 L176.4 14.2 L186.2 11.3 L192.1 5.9 L195.5 5.4 L203.8 0.0 L211.7 4.9 L219.0 5.9 L220.7 7.6 L221.7 12.0 L218.3 19.3 L216.3 29.1 L217.3 35.5 L222.2 44.8 L226.4 48.9 L238.1 53.3 L244.7 61.4 L244.2 68.3 L246.7 78.1 L243.2 89.8 L243.2 101.6 L247.7 111.8 L257.9 122.1 L252.1 144.6 L255.0 154.9 L253.0 170.6 L256.5 177.9 L263.8 184.8 L266.7 189.7 L260.4 209.7 L262.3 231.3 L257.9 246.9 L258.9 252.8 L264.3 261.1 L264.3 264.5 L257.9 286.6 L258.4 296.4 L263.3 303.7 L264.8 313.0 L271.1 326.2 L280.7 333.3 L288.5 334.8 L300.0 344.8 L290.7 353.6 L286.8 363.4 L282.2 367.6 L275.3 369.0 L244.0 367.6 L232.2 370.5 L209.7 383.2 L197.0 386.7 L190.1 390.6 L183.8 390.6 L177.9 393.0 L164.2 406.2 L147.6 407.7 L133.4 414.1 L113.8 418.5 L81.5 440.0 Z';
  const shapePts = PATH.replace(/[MZ]/g, '').trim().split(/\s*L\s*/).map(p => p.trim().split(/\s+/).map(Number)).filter(p => p.length === 2);
  // sample inside Ghana using a 2D canvas
  const cv = document.createElement('canvas'); cv.width = 300; cv.height = 440; const cx = cv.getContext('2d');
  cx.fillStyle = '#fff'; cx.beginPath(); shapePts.forEach(([x, y], i) => i ? cx.lineTo(x, y) : cx.moveTo(x, y)); cx.closePath(); cx.fill();
  const img = cx.getImageData(0, 0, 300, 440).data;
  const inside = (x, y) => img[((y | 0) * 300 + (x | 0)) * 4 + 3] > 128;
  const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
  const flow = new THREE.CatmullRomCurve3([new THREE.Vector3(-7, -2.2, 5), new THREE.Vector3(-2.5, 1.2, 1), new THREE.Vector3(2.2, -1, -4), new THREE.Vector3(-1.5, 1.6, -9), new THREE.Vector3(2.8, 0, -14), new THREE.Vector3(0, .4, -20)]);
  const attrs = Array.from({ length: 7 }, () => new Float32Array(N * 3));
  const aRand = new Float32Array(N), aU = new Float32Array(N), aG = new Float32Array(N);
  const cols = Math.ceil(Math.sqrt(N * 1.9)), rows = Math.ceil(N / cols);
  for (let i = 0; i < N; i++) {
    const r = rnd(); aRand[i] = r;
    // 0 cloud: flattened galaxy swirl
    { const a = rnd() * Math.PI * 2, rad = 1.2 + Math.pow(rnd(), .8) * 4.6, arm = Math.floor(rnd() * 3) * 2.09; const ang = a * .22 + arm + rad * .55;
      const x0 = Math.cos(ang) * rad + (rnd() - .5) * .7, z0 = Math.sin(ang) * rad + (rnd() - .5) * .7, y0 = (rnd() - .5) * 1.4 * (1 - rad / 7);
      attrs[0].set([x0, y0 * .9 + z0 * .42, z0 * .9 - y0 * .42], i * 3); }
    // 1 crowd: grid wall
    { const c = i % cols, rr = Math.floor(i / cols); attrs[1].set([(c / (cols - 1) - .5) * 14, (rr / (rows - 1) - .5) * 7.4, (rnd() - .5) * .25], i * 3); }
    // 2 ring
    { const u = rnd() * Math.PI * 2, v = rnd() * Math.PI * 2, R = 3.3, rr = .42 * Math.sqrt(rnd()); attrs[2].set([(R + rr * Math.cos(v)) * Math.cos(u), (R + rr * Math.cos(v)) * Math.sin(u), rr * Math.sin(v)], i * 3); }
    // 3 map
    { let x, y, t = 0; do { x = rnd() * 300; y = rnd() * 440; t++; } while (!inside(x, y) && t < 60); const w = toW(x, y); attrs[3].set([w[0], w[1], .32 + rnd() * .08], i * 3); }
    // 4 path river
    { const u = rnd(); aU[i] = u; const p = flow.getPoint(u); const a = rnd() * Math.PI * 2, rr = Math.sqrt(rnd()) * .42; attrs[4].set([p.x + Math.cos(a) * rr, p.y + Math.sin(a) * rr, p.z + (rnd() - .5) * .4], i * 3); }
    // 5 pillars
    { const k = Math.floor(rnd() * 3), H = [5.2, 6.4, 4.6][k], a = rnd() * Math.PI * 2, rr = .75 * Math.sqrt(rnd()); attrs[5].set([(k - 1) * 3.6 + Math.cos(a) * rr, -3.2 + rnd() * H, Math.sin(a) * rr], i * 3); }
    // 6 gauge semicircle band
    { const g = rnd(); aG[i] = g; const ang = Math.PI * (1 - g), R = 3.6 + (rnd() - .5) * .8; attrs[6].set([Math.cos(ang) * R, Math.sin(ang) * R - 1.2, (rnd() - .5) * .5], i * 3); }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(attrs[0].slice(), 3));
  attrs.forEach((a, k) => geo.setAttribute('p' + k, new THREE.BufferAttribute(a, 3)));
  geo.setAttribute('aRand', new THREE.BufferAttribute(aRand, 1)); geo.setAttribute('aU', new THREE.BufferAttribute(aU, 1)); geo.setAttribute('aG', new THREE.BufferAttribute(aG, 1));
  const U = {
    uTime: { value: 0 }, uFrom: { value: 0 }, uTo: { value: 0 }, uMix: { value: 0 },
    uDim: { value: 0 }, uCut: { value: 0 }, uRise: { value: 1 }, uGauge: { value: 0 }, uSize: { value: mobile ? 38 : 34 }, uPR: { value: PR },
    uMouse: { value: new THREE.Vector3(99, 99, 0) }, uMapFade: { value: 0 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `
      attribute vec3 p0; attribute vec3 p1; attribute vec3 p2; attribute vec3 p3; attribute vec3 p4; attribute vec3 p5; attribute vec3 p6;
      attribute float aRand; attribute float aU; attribute float aG;
      uniform float uTime, uFrom, uTo, uMix, uDim, uCut, uRise, uGauge, uSize, uPR, uMapFade; uniform vec3 uMouse;
      varying vec3 vColor; varying float vAlpha;
      float W(float k){ return (abs(uFrom-k)<.5 ? 1.-uMix : 0.) + (abs(uTo-k)<.5 ? uMix : 0.); }
      void main(){
        float w0=W(0.),w1=W(1.),w2=W(2.),w3=W(3.),w4=W(4.),w5=W(5.),w6=W(6.);
        float a = uTime*.04; mat2 R = mat2(cos(a),-sin(a),sin(a),cos(a));
        vec3 c0 = p0; c0.xz = R*c0.xz;
        float dim = step(aRand,.219)*uDim;
        vec3 c1 = p1; c1.z -= dim*3.; c1.y -= dim*1.4;
        vec3 c2 = p2; float side = sign(p2.x); c2.x += side*uCut*1.4; c2.y += side*uCut*.35; c2.z += side*uCut*.6;
        vec3 c5 = p5; c5.y = -3.2 + (p5.y+3.2)*uRise;
        vec3 pos = c0*w0 + c1*w1 + c2*w2 + p3*w3 + p4*w4 + c5*w5 + p6*w6;
        float j = .045 + w0*.12;
        pos += vec3(sin(uTime*.7+aRand*41.), cos(uTime*.6+aRand*29.), sin(uTime*.5+aRand*17.))*j;
        vec4 wp = modelMatrix*vec4(pos,1.);
        vec3 d = wp.xyz-uMouse; float dl = length(d.xy);
        wp.xy += normalize(d.xy+1e-4)*smoothstep(1.7,0.,dl)*.7;
        vec4 mv = viewMatrix*wp; gl_Position = projectionMatrix*mv;
        gl_PointSize = uSize*uPR*(.55+aRand*.75)*(1. + w0*.5 - w3*.25)/-mv.z;
        vec3 Y = vec3(1.,.72,.0), B = vec3(.26,.45,1.), Wt = vec3(.88,.92,1.), Gr = vec3(.22,.26,.4);
        vec3 col0 = mix(B, Y, step(.86,aRand));
        vec3 col1 = mix(Wt*.85, Gr, dim);
        vec3 col2 = mix(B, Y, step(0.,p2.x)*uCut);
        vec3 col3 = mix(Wt, B, .25+aRand*.2);
        vec3 col4 = mix(Y, B, smoothstep(.1,.95,aU));
        vec3 col5 = mix(B, Y, step(abs(p5.x),1.2));
        vec3 col6 = aG < uGauge ? Y : Gr*1.2;
        vColor = col0*w0+col1*w1+col2*w2+col3*w3+col4*w4+col5*w5+col6*w6;
        vAlpha = (.55 + aRand*.45) * (1. - dim*w1*.55) * (1. - w3*uMapFade*.72) * (1. + w0*.5);
      }`,
    fragmentShader: `varying vec3 vColor; varying float vAlpha;
      void main(){ float d = length(gl_PointCoord-.5); float a = smoothstep(.5,.0,d); gl_FragColor = vec4(vColor*a, a*vAlpha); }`,
  });
  const points = new THREE.Points(geo, mat); points.frustumCulled = false; root.add(points);

  /* ---- paper map, campuses, arcs ---- */
  const mapG = new THREE.Group(); root.add(mapG);
  const shape = new THREE.Shape(shapePts.map(([x, y]) => new THREE.Vector2(...toW(x, y))));
  const mapMats = [];
  [[0x061C66, -0.62, .22, .14], [0x0E2E9A, -0.36, .22, .07], [0x0A1F70, -0.1, .26, 0]].forEach(([col, z, depth, off]) => {
    const m = new THREE.MeshStandardMaterial({ color: col, roughness: .8, transparent: true, opacity: 0 }); mapMats.push(m);
    const mesh = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelThickness: .03, bevelSize: .03, bevelSegments: 2, curveSegments: 4 }), m);
    mesh.position.set(off, -off, z); mapG.add(mesh);
  });
  const haloTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(254,184,0,1)'); gr.addColorStop(.3, 'rgba(254,184,0,.4)'); gr.addColorStop(1, 'rgba(254,184,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
  const nodeGeo = new THREE.SphereGeometry(.09, 20, 14);
  const nodes = CAMPUSES.map((c, i) => {
    const [x, y] = toW(c.xy[0], c.xy[1]);
    const m = new THREE.Mesh(nodeGeo, new THREE.MeshBasicMaterial({ color: 0xFEB800, transparent: true, opacity: 0 }));
    m.position.set(x, y, .5); m.userData.i = i; mapG.add(m);
    const h = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0 }));
    h.position.copy(m.position); h.scale.set(.7, .7, 1); mapG.add(h); m.userData.h = h; return m;
  });
  const nd = (a, b) => nodes[a].position.distanceTo(nodes[b].position);
  const edges = [], inT = [0];
  while (inT.length < nodes.length) { let best = null; inT.forEach(a => nodes.forEach((_, b) => { if (inT.includes(b)) return; const d = nd(a, b); if (!best || d < best[2]) best = [a, b, d]; })); edges.push(best); inT.push(best[1]); }
  const arcs = edges.map(([a, b]) => { const A = nodes[a].position, B = nodes[b].position, M = A.clone().add(B).multiplyScalar(.5); M.z += .3 + A.distanceTo(B) * .25;
    const curve = new THREE.QuadraticBezierCurve3(A.clone(), M, B.clone()); const g = new THREE.BufferGeometry().setFromPoints(curve.getPoints(32));
    const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0x6E8FFF, transparent: true, opacity: 0 })); mapG.add(l); return { l, curve, wave: Math.max(CAMPUSES[a].wave, CAMPUSES[b].wave) }; });
  const pulses = reduce ? [] : arcs.map((a, k) => { const m = new THREE.Mesh(new THREE.SphereGeometry(.045, 8, 6), new THREE.MeshBasicMaterial({ color: 0xFEB800, transparent: true, opacity: 0 })); m.userData = { a, t: (k * .37) % 1 }; mapG.add(m); return m; });

  /* ---- post-processing glow (from three.js examples) ---- */
  let composer = null, bloom = null;
  if (!lowPower && THREE.EffectComposer && THREE.UnrealBloomPass) { // bloom off on mobile and low-power devices
    composer = new THREE.EffectComposer(renderer);
    composer.addPass(new THREE.RenderPass(scene, camera));
    bloom = new THREE.UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), .62, .5, .32); composer.addPass(bloom);
  }
  document.documentElement.dataset.bloom = composer ? 'on' : 'off'; // visible to tests and devtools

  /* ---- camera keyframes per state ---- */
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const CAM = [[V(0, 3.2, 12.5), V(0, 0, 0)], [V(0, -1.2, 13.5), V(0, 0, 0)], [V(0, 0, 11.5), V(0, 0, 0)], [V(0, -7.2, 17.5), V(0, -.7, 0)], [V(-1, 2, 11), V(0, 0, -6)], [V(0, 1.5, 15), V(0, .3, 0)], [V(0, .5, 13.5), V(0, .6, 0)]];
  const live = { from: 0, to: 0, mix: 0, flight: 0, offX: 0, litWave: -1, filter: null, dimCanvas: 1, focus: -1, interactive: false };
  api.params = live;
  const camPos = V(0, 0, 15), camLook = V(0, 0, 0);

  /* ---- 3D DOM anchors along the journey ---- */
  const anchorBox = $('#anchors');
  const ANCH = [[.08, '1', 'Join a chapter'], [.33, '2', 'Bootcamp'], [.58, '3', 'Real problem'], [.86, '4', 'Pitch and compete']].map(([u, n, t]) => {
    const el = document.createElement('div'); el.className = 'anchor'; el.innerHTML = `<b>${n}</b>${t}`; anchorBox.appendChild(el); return { el, p: flow.getPoint(u).add(V(0, .7, 0)) }; });
  const tmp = new THREE.Vector3();

  /* ---- interaction ---- */
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(-9, -9), plane = new THREE.Plane(V(0, 0, 1), 0), hitP = V(0, 0, 0);
  let hovered = null, dragging = null, spin = 0, tilt = 0, tgtSpin = 0, tgtTilt = 0;
  const tip = $('#tip');
  addEventListener('pointermove', e => {
    ptr.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
    if (dragging) { tgtSpin = dragging.s + (e.clientX - dragging.x) * .005; tgtTilt = Math.max(-.5, Math.min(.4, dragging.t + (e.clientY - dragging.y) * .004)); }
    else if (!reduce) { tgtSpin = ptr.x * .12; tgtTilt = -ptr.y * .06; }
    tip.style.left = e.clientX + 'px'; tip.style.top = e.clientY + 'px';
  }, { passive: true });
  addEventListener('pointerleave', () => ptr.set(-9, -9));
  const blocked = e => e.target.closest('a,button,input,select,textarea,label,.glass,header,#drawer,footer,.campuslist,.toasts');
  addEventListener('pointerdown', e => { if (!live.interactive || blocked(e)) return; dragging = { x: e.clientX, y: e.clientY, s: tgtSpin, t: tgtTilt }; });
  addEventListener('pointerup', e => { const moved = dragging && Math.hypot(e.clientX - dragging.x, e.clientY - dragging.y) > 5; dragging = null; if (!moved && hovered && !blocked(e) && api.onPick) api.onPick(hovered.userData.i); });

  function resize() {
    const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    if (composer) { composer.setSize(w, h); bloom.setSize(w, h); }
  }
  addEventListener('resize', resize); resize();

  const clock = new THREE.Clock();
  const lerp = (a, b, t) => a + (b - a) * t;
  function tick() {
    requestAnimationFrame(tick);
    const t = clock.getElapsedTime();
    U.uTime.value = reduce ? 0 : t;
    U.uFrom.value = live.from; U.uTo.value = live.to; U.uMix.value = live.mix;
    const wOf = k => (live.from === k ? 1 - live.mix : 0) + (live.to === k ? live.mix : 0);
    // camera blend between keyframes
    const A = CAM[live.from], B = CAM[live.to], m = live.mix;
    camPos.lerpVectors(A[0], B[0], m); camLook.lerpVectors(A[1], B[1], m);
    const fl = live.flight * 14 * wOf(4); camPos.z -= fl; camLook.z -= fl; camPos.x += Math.sin(live.flight * 3) * 1.2 * wOf(4);
    if (mobile) { camPos.z += 4; }
    camera.position.copy(camPos); camera.lookAt(camLook);
    spin = lerp(spin, tgtSpin, .06); tilt = lerp(tilt, tgtTilt, .06);
    root.rotation.set(tilt, spin * .6, 0); root.position.x = lerp(root.position.x, mobile ? 0 : live.offX, .06);
    // map, nodes, arcs
    const wm = wOf(3); U.uMapFade.value = wm;
    mapMats.forEach((mm, k) => mm.opacity = smooth(.35, 1, wm) * (k === 2 ? .92 : .85));
    mapG.visible = wm > .01; mapG.rotation.z = lerp(mapG.rotation.z, tgtSpin * .5 * (live.interactive ? 1 : 0), .1);
    const show = smooth(.6, 1, wm);
    nodes.forEach((n, i) => { const c = CAMPUSES[i];
      const lit = live.filter ? (live.filter === 'pilot' ? c.wave === 0 : live.filter === 'all' ? true : c.type === live.filter) : c.wave <= live.litWave;
      const isF = live.focus === i, isH = hovered === n;
      n.material.opacity = show * (lit || isF ? 1 : .28);
      n.material.color.set(lit || isF ? 0xFEB800 : 0x8FA6F0);
      const sc = isH || isF ? 1.9 : lit ? 1.25 : .9; n.scale.setScalar(lerp(n.scale.x, sc, .15));
      n.userData.h.material.opacity = show * (isH || isF ? 1 : lit ? .7 + (reduce ? 0 : Math.sin(t * 2 + i) * .2) : 0);
      n.userData.h.scale.setScalar(isH || isF ? 1.1 : .7); });
    arcs.forEach(a => { const on = live.filter ? 1 : (a.wave <= live.litWave ? 1 : .15); a.l.material.opacity = show * .75 * on; });
    pulses.forEach(p => { p.userData.t = (p.userData.t + .006) % 1; p.position.copy(p.userData.a.curve.getPoint(p.userData.t)); p.material.opacity = show * (p.userData.a.wave <= Math.max(live.litWave, live.filter ? 3 : -1) ? 1 : 0); });
    // anchors on the journey
    const wp = wOf(4) * (page === 'home' ? 1 : 0);
    ANCH.forEach(a => { tmp.copy(a.p).applyMatrix4(root.matrixWorld).project(camera); const vis = tmp.z < 1 && Math.abs(tmp.x) < 1.1 && Math.abs(tmp.y) < 1.1;
      a.el.style.opacity = vis ? smooth(.6, 1, wp) : 0; a.el.style.transform = `translate(${(tmp.x * .5 + .5) * innerWidth}px,${(-tmp.y * .5 + .5) * innerHeight}px) translate(-50%,-140%)`; });
    // pointer: repel particles + hover campuses
    ray.setFromCamera(ptr, camera);
    if (ray.ray.intersectPlane(plane, hitP)) U.uMouse.value.copy(hitP); else U.uMouse.value.set(99, 99, 0);
    let now = null;
    if (show > .5 && live.interactive) { const hit = ray.intersectObjects(nodes)[0]; now = hit ? hit.object : null; }
    if (now !== hovered) { hovered = now; document.body.style.cursor = hovered ? 'pointer' : '';
      if (hovered) { const c = CAMPUSES[hovered.userData.i]; tip.innerHTML = `<b>${esc(c.city)}</b>${esc(c.name)}`; tip.style.opacity = 1; } else tip.style.opacity = 0; }
    if (composer) composer.render(); else renderer.render(scene, camera);
  }
  tick();

  api.set = (from, to, mix) => { live.from = from; live.to = to; live.mix = mix; };
  api.u = U;
  api.morphTo = (state, opts = {}) => {
    const cur = live.mix > .5 ? live.to : live.from;
    Object.assign(live, { from: cur, to: state, mix: 0 });
    const done = () => { Object.assign(live, { from: state, to: state, mix: 0 }); };
    if (!G || reduce) { done(); return; }
    gsap.killTweensOf(live);
    gsap.to(live, { mix: 1, duration: opts.dur || 1.6, ease: 'power3.inOut', onComplete: done });
  };
  return api;
})();

/* ================= PAGE SETUP ================= */
// state, camera offsetX, canvas opacity, interactive
const SCENE = {
  about: [2, 3.2, .7], programs: [5, 3.6, .6], opportunities: [4, 0, .65], network: [3, 4.5, 1, true], partners: [2, 3.2, .7],
  donate: [6, 2.9, 1], join: [3, 4.5, 1, true], contact: [0, 3, .8], news: [1, 0, .5], privacy: [1, 0, .35],
};
const wipe = $$('#wipe i');

function setupPage(p) {
  const rail = $('#rail'), hint = $('#scrollhint');
  const L = World.params;
  if (p === 'home') { $('#gl').style.opacity = 1; L.offX = 0; L.interactive = true; L.filter = null; L.focus = -1; buildStory(); }
  else {
    if (rail) rail.remove(); if (hint) hint.remove();
    const [st, ox, op, inter] = SCENE[p] || SCENE.news;
    // on phones the camera can't offset sideways, so the scene sits behind the text: dim it
    $('#gl').style.opacity = mobile && ox ? op * .55 : op; L.offX = ox; L.interactive = !!inter; L.flight = 0; L.focus = -1;
    L.filter = (p === 'network' || p === 'join') ? 'all' : null; L.litWave = 3;
    World.u.uDim.value = 0; World.u.uCut.value = p === 'partners' ? 1 : 0; World.u.uRise.value = 1;
    if (p === 'donate') updateDonate(); else World.u.uGauge.value = .65;
    World.morphTo(st);
  }
  animateIn();
  if (ST) requestAnimationFrame(() => ScrollTrigger.refresh());
}
function animateIn() {
  const els = $$('main .reveal');
  if (!G || reduce) { els.forEach(el => { el.style.opacity = 1; el.style.transform = 'none'; }); return; }
  gsap.fromTo($$('main .split .w > span'), { yPercent: 115 }, { yPercent: 0, duration: 1.05, ease: 'power4.out', stagger: .05, delay: .35 });
  els.forEach(el => {
    gsap.set(el, { opacity: 0, y: 26 });
    if (ST) ScrollTrigger.create({ trigger: el, start: 'top 90%', once: true, onEnter: () => gsap.to(el, { opacity: 1, y: 0, duration: .85, ease: 'power3.out' }) });
    else gsap.to(el, { opacity: 1, y: 0, duration: .8 });
  });
}

/* ================= PAGE WIPE: entry on load, exit before navigation ================= */
function wipeIn() {
  if (!G || reduce) { docEl.classList.remove('wipe-cover'); return; }
  gsap.set(wipe, { scaleY: 1, transformOrigin: 'top' }); docEl.classList.remove('wipe-cover');
  gsap.to(wipe, { scaleY: 0, transformOrigin: 'top', duration: .5, ease: 'power3.out', stagger: .045, delay: .05 });
}
function navigate(href) {
  closeDrawer();
  if (!G || reduce) { location.assign(href); return; }
  gsap.timeline({ onComplete: () => location.assign(href) })
    .to(wipe, { scaleY: 1, transformOrigin: 'bottom', duration: .42, ease: 'power3.in', stagger: .045 });
}
document.addEventListener('click', e => {
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const a = e.target.closest('a[href]'); if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin || /^\/(static|media|secretariat-admin)\//.test(url.pathname)) return;
  if (url.pathname === location.pathname && url.search === location.search) { closeDrawer(); return; } // same page: let the hash scroll
  e.preventDefault(); navigate(url.href);
});
addEventListener('pageshow', e => { if (e.persisted && G) gsap.set(wipe, { scaleY: 0 }); }); // back/forward cache

/* ================= HEADER, MEGA MENU, DRAWER ================= */
const header = $('header'); const onS = () => header.classList.toggle('solid', scrollY > 30); addEventListener('scroll', onS, { passive: true }); onS();
const tops = $$('.menu button.top');
const closeMenus = except => tops.forEach(b => { if (b !== except) { b.setAttribute('aria-expanded', 'false'); b.parentElement.classList.remove('open'); } });
tops.forEach(b => b.addEventListener('click', () => {
  const open = b.getAttribute('aria-expanded') !== 'true'; closeMenus(b);
  b.setAttribute('aria-expanded', String(open)); b.parentElement.classList.toggle('open', open);
  if (open) { const first = $('.drop a', b.parentElement); if (first && b.matches(':focus-visible')) first.focus(); }
}));
document.addEventListener('click', e => { if (!e.target.closest('.menu > li')) closeMenus(); });
const drawer = $('#drawer'), burger = $('.burger');
function closeDrawer() { if (!drawer.classList.contains('open')) return; drawer.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); drawer.inert = true; burger.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; burger.focus(); }
drawer.inert = true;
burger.addEventListener('click', () => { drawer.classList.add('open'); drawer.removeAttribute('aria-hidden'); drawer.inert = false; burger.setAttribute('aria-expanded', 'true'); document.body.style.overflow = 'hidden'; $('.x', drawer).focus(); });
$('.x', drawer).addEventListener('click', closeDrawer);
addEventListener('keydown', e => { if (e.key !== 'Escape') return; closeDrawer(); const openB = tops.find(b => b.getAttribute('aria-expanded') === 'true'); closeMenus(); if (openB) openB.focus(); });
setTimeout(() => $$('.toast').forEach(t => G && !reduce ? gsap.to(t, { opacity: 0, y: -10, duration: .4, onComplete: () => t.remove() }) : t.remove()), 9000);

/* ================= HOME STORY (home page only) ================= */
const chapters = $$('.chapter');
const NEXT = [1, 2, 3, 4, 5, 6, 3, 3];
const STATE = [0, 1, 2, 3, 4, 5, 6, 3];
const CHOFF = [3.4, 3, -3, 4.3, -1.5, 3, -3, 0];
const WAVE_TXT = ['pilot chapters in Year 1', 'chapters by Year 2', 'chapters by Year 3', 'chapters by Year 5'];
const counted = new WeakSet();
function countUp(el) { if (!el || counted.has(el)) return; counted.add(el); const to = +el.dataset.to; const f = v => Math.round(v).toLocaleString('en-US');
  if (!G || reduce) { el.textContent = f(to); return; } const o = { v: 0 }; gsap.to(o, { v: to, duration: 2.2, ease: 'power3.out', onUpdate: () => el.textContent = f(o.v) }); }
function story(i, u) {
  const hold = .6, L = World.params, Uu = World.u;
  const p = Math.min(1, u / hold), tr = u > hold ? smooth(0, 1, (u - hold) / (1 - hold)) : 0;
  World.params.offX = CHOFF[i] + (u > hold && i < 7 ? (CHOFF[i + 1] - CHOFF[i]) * tr : 0);
  if (World.ok) World.set(STATE[i], NEXT[i] === STATE[i] ? STATE[i] : NEXT[i], NEXT[i] === STATE[i] ? 0 : tr);
  Uu.uDim.value = i > 1 ? 1 : i === 1 ? smooth(.15, .7, p) : 0;
  Uu.uCut.value = i > 2 ? 1 : i === 2 ? smooth(.4, .85, p) : 0;
  const wave = i < 3 ? -1 : i === 3 ? (p < .25 ? 0 : p < .5 ? 1 : p < .75 ? 2 : 3) : 3;
  L.litWave = wave;
  if (i === 3) { const k = Math.max(0, wave); $('#waveN').textContent = WAVES[k]; $('#waveL').textContent = WAVE_TXT[k]; }
  L.flight = i < 4 ? 0 : i === 4 ? p : 1;
  Uu.uRise.value = i < 5 ? .05 : i === 5 ? smooth(0, .7, p) : 1;
  const g = i < 6 ? 0 : i === 6 ? (p < .35 ? smooth(.05, .3, p) * .65 : p < .65 ? .65 + smooth(.4, .6, p) * .17 : .82 + smooth(.7, .9, p) * .16) : .98;
  Uu.uGauge.value = g;
  if (i === 6) { $('#gaugeN').textContent = Math.round(g * 100) + '%'; $('#gaugeL').textContent = g < .66 ? 'of costs earned by TIEN, base plan' : g < .83 ? 'with half of the new business lines' : 'with all the new business lines'; }
  L.filter = i === 7 ? 'all' : null;
  $$('#rail button').forEach((b, k) => { b.classList.toggle('on', k === i); if (k === i) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
  const hint = $('#scrollhint'); if (hint) hint.style.opacity = i === 0 && u < .2 ? 1 : 0;
  if (i === 1) countUp($('#c1 .count'));
}
function buildStory() {
  const rail = $('#rail');
  if (rail) {
    rail.innerHTML = chapters.map((c, i) => `<button type="button" aria-label="${esc(c.dataset.title)}" data-i="${i}"><span>${esc(c.dataset.title)}</span></button>`).join('');
    $$('#rail button').forEach(b => b.addEventListener('click', () => { const c = chapters[+b.dataset.i]; const y = c.getBoundingClientRect().top + scrollY + innerHeight * .35; scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' }); }));
  }
  World.params.offX = 0;
  // without JS the chapters already show their final text; with JS they start from the story's first frame
  const c1 = $('#c1 .count'); if (c1 && G && !reduce) c1.textContent = '0';
  if (!ST) { story(0, 0); countUp(c1); return; }
  chapters.forEach((c, i) => homeTriggers.push(ScrollTrigger.create({ trigger: c, start: 'top top', end: 'bottom bottom', onUpdate: s => story(i, s.progress) })));
  story(0, 0);
}

/* ================= NETWORK PAGE ================= */
function focusCampus(i) {
  World.params.focus = i;
  $$('#campusList .campus').forEach(b => { const on = idxOf(b.dataset.id) === i; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
  const c = CAMPUSES[i]; if (c) { const tip = $('#tip'); tip.innerHTML = `<b>${esc(c.city)}</b>${esc(c.name)}`; }
}
if (page === 'network') {
  $$('#netFilters .chip').forEach(ch => ch.addEventListener('click', () => {
    $$('#netFilters .chip').forEach(o => o.setAttribute('aria-pressed', String(o === ch)));
    const f = ch.dataset.f; World.params.filter = f; World.params.focus = -1;
    $$('#campusList .campus').forEach(b => b.hidden = !(f === 'all' || (f === 'pilot' ? b.dataset.wave === '0' : b.dataset.type === f)));
  }));
  $$('#campusList .campus').forEach(b => b.addEventListener('click', () => focusCampus(idxOf(b.dataset.id))));
  const want = new URLSearchParams(location.search).get('focus');
  if (want && idxOf(want) > -1) setTimeout(() => { focusCampus(idxOf(want)); const b = $(`#campusList .campus[data-id="${CSS.escape(want)}"]`); if (b) b.scrollIntoView({ block: 'nearest' }); }, 900);
}
World.onPick = i => {
  if (page === 'join') { pickCampus(i); return; }
  if (page !== 'network') { navigate(`/network/?focus=${encodeURIComponent(CAMPUSES[i].id)}`); return; }
  focusCampus(i); const b = $(`#campusList .campus[data-id="${CAMPUSES[i].id}"]`); if (b) { b.hidden = false; b.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' }); }
};

/* ================= DONATE ================= */
const COST = +(document.body.dataset.costPerStudent || 460);
let amount = 0;
const donateForm = $('#donateForm');
function readAmount() {
  if (!donateForm) return 0; const el = donateForm.elements; const pick = $('input[name="preset"]:checked', donateForm);
  if (!pick) return 0; if (pick.value === 'other') return parseFloat((el.custom.value || '').replace(/,/g, '')) || 0; return +pick.value;
}
function updateDonate() {
  if (!donateForm) return;
  amount = readAmount(); const students = amount / COST;
  const fmt = n => n.toLocaleString('en-US', { maximumFractionDigits: 2 });
  $('#impact').innerHTML = !amount ? 'Choose an amount to see your impact.' : students >= 1 ? `Your gift of <b>GHS ${fmt(amount)}</b> puts <b>${Math.floor(students)} student${Math.floor(students) > 1 ? 's' : ''}</b> through intensive training.` : `Your gift covers <b>${Math.round(students * 100)}%</b> of the cost of training one student. Every cedi moves someone closer.`;
  $('#donateBtn').innerHTML = amount ? `Give GHS ${fmt(amount)} securely <span class="arrow" aria-hidden="true">&rarr;</span>` : 'Continue to payment';
  if (World.ok && page === 'donate') { const g = Math.min(.98, .08 + students / 10 * .9); if (G && !reduce) gsap.to(World.u.uGauge, { value: g, duration: .9, ease: 'power3.out' }); else World.u.uGauge.value = g; }
}
if (donateForm) {
  const el = donateForm.elements, customWrap = $('#customWrap'), campusPick = $('#campusPick');
  const sync = () => {
    const pick = $('input[name="preset"]:checked', donateForm);
    customWrap.hidden = !(pick && pick.value === 'other') && !$('#customWrap [aria-invalid]');
    campusPick.hidden = el.designation.value !== 'chapter' && !$('#campusPick [aria-invalid]');
    updateDonate();
  };
  $$('input[name="preset"]', donateForm).forEach(r => r.addEventListener('change', () => { sync(); if (r.value === 'other') el.custom.focus(); }));
  el.custom.addEventListener('input', updateDonate);
  el.designation.addEventListener('change', sync);
  sync();
}

/* ================= JOIN WIZARD (4 steps, server-validated) ================= */
const joinForm = $('#joinForm');
const ROLE_REQ = {
  student: ['full_name', 'email', 'phone', 'institution', 'institution_type'],
  ambassador: ['full_name', 'email', 'phone', 'institution', 'institution_type', 'motivation'],
  institution: ['full_name', 'email', 'phone', 'institution', 'institution_type', 'region'],
  mentor: ['full_name', 'email', 'phone', 'organisation', 'expertise'],
};
let step = 0;
const role = () => { const r = joinForm && $('input[name="role"]:checked', joinForm); return r ? r.value : 'student'; };
function pickCampus(i) {
  const sel = joinForm && joinForm.elements.institution; if (!sel || !CAMPUSES[i]) return;
  sel.value = String(CAMPUSES[i].id); sel.dispatchEvent(new Event('change'));
  sel.style.borderColor = 'var(--yellow)'; setTimeout(() => sel.style.borderColor = '', 1200);
}
if (joinForm) {
  const el = joinForm.elements, stepErr = $('#stepErr');
  const applyRole = () => {
    const r = role();
    $$('.role-only', joinForm).forEach(g => { g.hidden = !g.dataset.roles.split(' ').includes(r); });
    World.params.interactive = r !== 'mentor';
  };
  const syncInst = () => {
    const sel = el.institution; if (!sel) return;
    $('#instOther').hidden = sel.value !== 'other' && !$('#instOther [aria-invalid]');
    World.params.focus = idxOf(sel.value);
  };
  $$('input[name="role"]', joinForm).forEach(r => r.addEventListener('change', applyRole));
  el.institution.addEventListener('change', syncInst);
  const visible = n => { const f = el[n]; return f && !f.closest('[hidden]'); };
  const validEmail = v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  function checkStep1() {
    const bad = [];
    let req = ROLE_REQ[role()].slice(); if (req.includes('institution') && el.institution.value === 'other') { req = req.filter(n => n !== 'institution').concat('institution_other'); }
    req.forEach(n => { const f = el[n]; if (!f) return; const v = f.value.trim(); const ok = n === 'email' ? validEmail(v) : v !== '';
      f.setAttribute('aria-invalid', String(!ok)); if (!ok) bad.push(f); });
    stepErr.textContent = bad.length ? 'Please check the highlighted fields.' : '';
    if (bad.length) bad[0].focus(); return !bad.length;
  }
  function buildReview() {
    const rows = [['Joining as', $('input[name="role"]:checked', joinForm).closest('label').querySelector('b').textContent]];
    $$('[data-s="1"] .field', joinForm).forEach(fd => {
      if (fd.closest('[hidden]')) return; const f = $('input,select,textarea', fd); if (!f || !f.value.trim()) return;
      const label = ($('label', fd) || fd).childNodes[0].textContent.trim();
      const val = f.tagName === 'SELECT' ? f.options[f.selectedIndex].text : f.value.trim();
      rows.push([label, val]);
    });
    const ints = $$('input[name="interests"]:checked', joinForm).map(c => c.value); if (ints.length) rows.push(['Interested in', ints.join(', ')]);
    $('#review').innerHTML = rows.map(([k, v]) => `<div><span>${esc(k)}</span><b style="font-weight:500;text-align:right">${esc(v)}</b></div>`).join('');
  }
  function showStep(n, focus = true) {
    step = n; $$('.fstep', joinForm).forEach(s => s.classList.toggle('on', +s.dataset.s === n));
    $$('.steps i').forEach((b, k) => b.classList.toggle('on', k <= n));
    $('#back').style.visibility = n === 0 ? 'hidden' : 'visible';
    $('#next').innerHTML = n === 3 ? 'Submit application <span class="arrow" aria-hidden="true">&rarr;</span>' : 'Continue <span class="arrow" aria-hidden="true">&rarr;</span>';
    $('#stepLabel').textContent = `Step ${n + 1} of 4`;
    if (n === 3) buildReview();
    if (focus) { const h = $(`.fstep[data-s="${n}"] [data-step-title]`, joinForm); if (h) h.focus({ preventScroll: true }); }
  }
  $('#next').addEventListener('click', e => {
    if (step === 3) { // stays type="button" so Continue on step 3 can never submit early
      if (!el.consent_given.checked) { stepErr.textContent = 'Please confirm you agree to the privacy policy.'; el.consent_given.focus(); return; }
      joinForm.requestSubmit(); return;
    }
    stepErr.textContent = '';
    if (step === 1 && !checkStep1()) return;
    showStep(step + 1);
  });
  $('#back').addEventListener('click', () => { stepErr.textContent = ''; showStep(Math.max(0, step - 1)); });
  applyRole(); syncInst();
  showStep(+(joinForm.dataset.startStep || 0), joinForm.dataset.startStep !== undefined && joinForm.dataset.hasErrors === '1');
  if (joinForm.dataset.hasErrors === '1') { const bad = $('[aria-invalid="true"]', joinForm); if (bad && !bad.closest('[hidden]')) bad.focus(); }
}

/* ================= START ================= */
wipeIn();
setupPage(page);
if (G && !reduce && page === 'home') { gsap.from('#c0 .kicker,#c0 .lead,#c0 .cta-row', { opacity: 0, y: 20, duration: .9, stagger: .12, delay: .6 }); }
} catch (err) {
  docEl.classList.remove('wipe-cover'); docEl.classList.add('reveal-fallback');
  console.error('[TIEN] front-end enhancement failed; page left in its no-JS state.', err);
}
})();
