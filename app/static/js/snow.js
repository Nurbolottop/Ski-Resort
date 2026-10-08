/* =============================================================================
   Тоо-Ашуу — снегопад на canvas: три плана глубины, ветер, реакция на курсор.
   Пауза в фоновой вкладке, выключатель с запоминанием, без снега при reduced motion.
   ============================================================================= */
(function () {
    'use strict';

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var KEY = 'snow-off';
    var off = false;
    try { off = localStorage.getItem(KEY) === '1'; } catch (e) { /* приватный режим */ }

    var canvas = document.createElement('canvas');
    canvas.className = 'snow-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    var ctx = canvas.getContext('2d');

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'snow-toggle';
    toggle.setAttribute('aria-label', 'Снегопад');
    toggle.innerHTML = '<svg viewBox="0 0 24 24" class="icon"><use href="#i-snow"></use></svg>';

    var W = 0, H = 0, dpr = 1, flakes = [], running = false, last = 0;
    var wind = 0, windTarget = 0, mouseX = -9999, mouseY = -9999;

    // Планы: дальний (мелкий, размытый, медленный) → ближний (крупный, быстрый)
    var LAYERS = [
        { share: .62, r: [0.5, 1.1], v: [10, 20], a: [.18, .38], sway: 10 },
        { share: .3, r: [1.1, 1.9], v: [20, 36], a: [.3, .55], sway: 16 },
        { share: .08, r: [1.9, 2.8], v: [36, 56], a: [.45, .7], sway: 24 },
    ];

    function rand(a, b) { return a + Math.random() * (b - a); }

    function makeFlake(layer, anywhere) {
        var L = LAYERS[layer];
        return {
            layer: layer,
            x: Math.random() * W,
            y: anywhere ? Math.random() * H : -10,
            r: rand(L.r[0], L.r[1]),
            v: rand(L.v[0], L.v[1]),
            a: rand(L.a[0], L.a[1]),
            phase: Math.random() * Math.PI * 2,
            freq: rand(.4, 1.1),
            sway: L.sway * rand(.6, 1.2),
            dx: 0,
        };
    }

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        W = window.innerWidth; H = window.innerHeight;
        canvas.width = W * dpr; canvas.height = H * dpr;
        canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        var total = Math.round(Math.min(70, Math.max(24, W * H / 30000)));
        if (W < 640) total = Math.round(total * .6);
        flakes = [];
        LAYERS.forEach(function (L, i) {
            for (var k = 0; k < Math.round(total * L.share); k++) flakes.push(makeFlake(i, true));
        });
    }

    // Мягкая снежинка: радиальный градиент
    var sprites = {};
    function sprite(r) {
        var key = Math.round(r * 4);
        if (sprites[key]) return sprites[key];
        var s = Math.ceil(r * 4), c = document.createElement('canvas');
        c.width = c.height = s * 2;
        var g = c.getContext('2d'), grd = g.createRadialGradient(s, s, 0, s, s, s);
        grd.addColorStop(0, 'rgba(255,255,255,1)');
        grd.addColorStop(.35, 'rgba(240,248,255,.85)');
        grd.addColorStop(1, 'rgba(220,235,255,0)');
        g.fillStyle = grd; g.fillRect(0, 0, s * 2, s * 2);
        return (sprites[key] = c);
    }

    function frame(t) {
        if (!running) return;
        var dt = Math.min(.05, (t - last) / 1000 || 0);
        last = t;
        // порывы ветра
        if (Math.random() < .004) windTarget = rand(-28, 34);
        wind += (windTarget - wind) * .01;

        ctx.clearRect(0, 0, W, H);
        for (var i = 0; i < flakes.length; i++) {
            var f = flakes[i];
            var depth = .5 + f.layer * .35;
            f.phase += f.freq * dt;
            // отталкивание от курсора (только ближние планы)
            var mx = f.x - mouseX, my = f.y - mouseY, d2 = mx * mx + my * my;
            if (f.layer > 0 && d2 < 14000) {
                var force = (1 - d2 / 14000) * 60 * f.layer;
                f.dx += (mx / Math.sqrt(d2 + 1)) * force * dt;
            }
            f.dx *= .96;
            f.x += (Math.sin(f.phase) * f.sway * .6 + wind * depth + f.dx) * dt;
            f.y += f.v * dt;
            if (f.y > H + 10) { flakes[i] = makeFlake(f.layer, false); continue; }
            if (f.x > W + 10) f.x = -10; else if (f.x < -10) f.x = W + 10;
            var spr = sprite(f.r);
            ctx.globalAlpha = f.a;
            ctx.drawImage(spr, f.x - spr.width / 2, f.y - spr.height / 2);
        }
        ctx.globalAlpha = 1;
        requestAnimationFrame(frame);
    }

    function start() {
        if (running || off || document.hidden) return;
        running = true; canvas.style.opacity = '1';
        last = performance.now();
        requestAnimationFrame(frame);
    }

    function stop() {
        running = false;
    }

    function setOff(value) {
        off = value;
        try { localStorage.setItem(KEY, value ? '1' : '0'); } catch (e) { /* ignore */ }
        toggle.classList.toggle('is-off', value);
        toggle.title = value ? 'Включить снегопад' : 'Выключить снегопад';
        if (value) { stop(); canvas.style.opacity = '0'; } else { start(); }
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(canvas);
        document.body.appendChild(toggle);
        resize();
        setOff(off);
        toggle.addEventListener('click', function () { setOff(!off); });
        var rt;
        window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(resize, 200); });
        window.addEventListener('pointermove', function (e) { mouseX = e.clientX; mouseY = e.clientY; }, { passive: true });
        document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); else start(); });
    });
})();
