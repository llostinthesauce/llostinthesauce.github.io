(function () {
    // Normalize the auto-generated data ([src, w, h] tuples) to objects with safe fallbacks.
    var rawData = window.allImagesData || [];
    var images = [];
    for (var i = 0; i < rawData.length; i++) {
        var entry = rawData[i];
        if (typeof entry === 'string') {
            images.push({ src: entry, w: 1, h: 1, thumb: entry });
        } else if (entry && entry.length >= 3) {
            images.push({
                src: entry[0],
                w: entry[1] || 1,
                h: entry[2] || 1,
                thumb: entry[3] || entry[0]
            });
        }
    }

    var viewport = document.getElementById('canvas-viewport');
    var world = document.getElementById('canvas-world');
    var hud = {
        count: document.getElementById('canvas-count'),
        zoom: document.getElementById('canvas-zoom')
    };
    var hint = document.getElementById('canvas-hint');

    if (!viewport || !world) return;
    if (hud.count) hud.count.textContent = images.length;
    if (!images.length) {
        world.textContent = 'no images';
        return;
    }

    // ---- layout config ----
    var ROW_H = 200;
    var GAP = 8;
    var ROW_PITCH = ROW_H + GAP;
    var MIN_CELL_W = 110;
    var MAX_CELL_W = 460;

    var MIN_SCALE = 0.2;
    var MAX_SCALE = 3.5;
    var MOMENTUM_FRICTION = 0.93;
    var MOMENTUM_STOP = 0.4;
    var CLICK_MAX_MOVE = 8;
    var CLICK_MAX_TIME = 450;
    var VELOCITY_WINDOW_MS = 90;
    var WHEEL_PAN_FACTOR = 1.0;
    var WHEEL_ZOOM_FACTOR = 0.012;
    var MAX_CELLS_IN_DOM = 800;
    var K_LAYOUTS = 8;

    // ---- precomputed row layouts ----
    // Each layout: { order: [imgIdx,...], cellStart: [...], cellWidth: [...], totalW }
    // K_LAYOUTS different shuffles so rows visually differ; row r uses layout (r mod K).
    var layouts = [];

    function widthForImage(img) {
        var aspect = img.w / img.h;
        if (!isFinite(aspect) || aspect <= 0) aspect = 1;
        var w = ROW_H * aspect;
        if (w < MIN_CELL_W) w = MIN_CELL_W;
        if (w > MAX_CELL_W) w = MAX_CELL_W;
        return w;
    }

    function buildLayouts() {
        for (var k = 0; k < K_LAYOUTS; k++) {
            var order = new Array(images.length);
            for (var i = 0; i < images.length; i++) order[i] = i;

            // Fisher-Yates seeded by k (deterministic per layout).
            var seed = ((k + 1) * 2654435761) | 0;
            for (var i2 = order.length - 1; i2 > 0; i2--) {
                seed = (seed * 1103515245 + 12345) | 0;
                var j = Math.abs(seed) % (i2 + 1);
                var t = order[i2]; order[i2] = order[j]; order[j] = t;
            }

            var cellStart = new Float64Array(order.length);
            var cellWidth = new Float64Array(order.length);
            var cursor = 0;
            for (var n = 0; n < order.length; n++) {
                var w = widthForImage(images[order[n]]);
                cellStart[n] = cursor;
                cellWidth[n] = w;
                cursor += w + GAP;
            }
            layouts.push({ order: order, cellStart: cellStart, cellWidth: cellWidth, totalW: cursor });
        }
    }

    buildLayouts();

    function layoutFor(row) {
        var idx = ((row % K_LAYOUTS) + K_LAYOUTS) % K_LAYOUTS;
        return layouts[idx];
    }

    // Hash row -> deterministic horizontal offset into the row's totalW.
    function rowOffset(row, totalW) {
        var s = ((row | 0) * 374761393) | 0;
        s = ((s ^ (s >>> 13)) * 1274126177) | 0;
        s = s ^ (s >>> 16);
        return ((s >>> 0) / 4294967296) * totalW;
    }

    // Binary search: largest index i where layout.cellStart[i] <= x.
    function firstCellAtOrBefore(layout, x) {
        var lo = 0, hi = layout.cellStart.length - 1;
        if (x <= 0) return 0;
        if (x >= layout.cellStart[hi]) return hi;
        while (lo < hi) {
            var mid = (lo + hi + 1) >>> 1;
            if (layout.cellStart[mid] <= x) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }

    // ---- pan + zoom state. Screen pos = world * scale + offset. ----
    var offsetX = 0;
    var offsetY = 0;
    var scale = 1;

    // ---- cell DOM cache ----
    var liveCells = new Map(); // key -> element
    var cellPool = [];

    function acquireCell() {
        if (cellPool.length) return cellPool.pop();
        var el = document.createElement('a');
        el.className = 'canvas-cell';
        el.target = '_blank';
        el.rel = 'noopener';
        el.draggable = false;
        return el;
    }

    function releaseCell(el) {
        el.style.backgroundImage = '';
        el.removeAttribute('href');
        if (el.parentNode) el.parentNode.removeChild(el);
        if (cellPool.length < 120) cellPool.push(el);
    }

    var pendingRender = false;
    function scheduleRender() {
        if (pendingRender) return;
        pendingRender = true;
        requestAnimationFrame(function () {
            pendingRender = false;
            render();
        });
    }

    function applyTransform() {
        world.style.transform = 'translate3d(' + offsetX + 'px,' + offsetY + 'px,0) scale(' + scale + ')';
        if (hud.zoom) hud.zoom.textContent = Math.round(scale * 100) + '%';
    }

    function render() {
        applyTransform();

        var vw = viewport.clientWidth;
        var vh = viewport.clientHeight;

        // World-space viewport bounds.
        var worldLeft = -offsetX / scale;
        var worldTop = -offsetY / scale;
        var worldRight = (vw - offsetX) / scale;
        var worldBottom = (vh - offsetY) / scale;

        var rowMin = Math.floor(worldTop / ROW_PITCH) - 1;
        var rowMax = Math.ceil(worldBottom / ROW_PITCH) + 1;

        var seen = new Set();
        var emitted = 0;

        for (var r = rowMin; r <= rowMax; r++) {
            if (emitted >= MAX_CELLS_IN_DOM) break;

            var layout = layoutFor(r);
            var W = layout.totalW;
            var rOff = rowOffset(r, W);

            // Shifted viewport in row-local coordinates.
            var vL = worldLeft + rOff;
            var vR = worldRight + rOff;

            var repStart = Math.floor(vL / W);
            var repEnd = Math.floor(vR / W);

            for (var rep = repStart; rep <= repEnd && emitted < MAX_CELLS_IN_DOM; rep++) {
                var localL = vL - rep * W;
                var localR = vR - rep * W;
                if (localL < 0) localL = 0;
                if (localR > W) localR = W;

                var first = firstCellAtOrBefore(layout, localL);
                for (var i = first; i < layout.cellStart.length && emitted < MAX_CELLS_IN_DOM; i++) {
                    if (layout.cellStart[i] >= localR) break;

                    var cellWX = rep * W + layout.cellStart[i] - rOff;
                    var cellWY = r * ROW_PITCH;
                    var cellW = layout.cellWidth[i];

                    var key = r + ':' + rep + ':' + i;
                    seen.add(key);
                    emitted++;
                    if (liveCells.has(key)) continue;

                    var imgIdx = layout.order[i];
                    var entryRef = images[imgIdx];
                    var el = acquireCell();
                    el.style.left = cellWX + 'px';
                    el.style.top = cellWY + 'px';
                    el.style.width = cellW + 'px';
                    el.style.height = ROW_H + 'px';
                    el.style.backgroundImage = 'url("' + entryRef.thumb + '")';
                    el.href = entryRef.src;
                    el.title = entryRef.src;
                    world.appendChild(el);
                    liveCells.set(key, el);
                }
            }
        }

        liveCells.forEach(function (el, key) {
            if (!seen.has(key)) {
                releaseCell(el);
                liveCells.delete(key);
            }
        });
    }

    // ---- pointer (drag + pinch) ----

    var pointers = new Map();
    var lastSingleX = 0;
    var lastSingleY = 0;
    var pinchStartDist = 0;
    var pinchStartScale = 1;
    var pinchMidWorldX = 0;
    var pinchMidWorldY = 0;
    var dragMoved = 0;
    var dragStartTime = 0;
    var dragStartX = 0;
    var dragStartY = 0;
    var dragTarget = null;

    var velocitySamples = [];
    var momentumVX = 0;
    var momentumVY = 0;
    var momentumRunning = false;

    function fadeHint() {
        if (hint && !hint.classList.contains('fade')) hint.classList.add('fade');
    }

    function clampScale(s) {
        return Math.max(MIN_SCALE, Math.min(MAX_SCALE, s));
    }

    function pushVelocity(x, y) {
        var t = performance.now();
        velocitySamples.push({ x: x, y: y, t: t });
        var cutoff = t - VELOCITY_WINDOW_MS;
        while (velocitySamples.length > 1 && velocitySamples[0].t < cutoff) velocitySamples.shift();
    }

    function computeVelocity() {
        if (velocitySamples.length < 2) return { x: 0, y: 0 };
        var first = velocitySamples[0];
        var last = velocitySamples[velocitySamples.length - 1];
        var dt = last.t - first.t;
        if (dt <= 0) return { x: 0, y: 0 };
        return { x: (last.x - first.x) / dt * 16, y: (last.y - first.y) / dt * 16 };
    }

    function startMomentum() {
        if (momentumRunning) return;
        momentumRunning = true;
        var step = function () {
            if (!momentumRunning) return;
            offsetX += momentumVX;
            offsetY += momentumVY;
            momentumVX *= MOMENTUM_FRICTION;
            momentumVY *= MOMENTUM_FRICTION;
            scheduleRender();
            if (Math.abs(momentumVX) < MOMENTUM_STOP && Math.abs(momentumVY) < MOMENTUM_STOP) {
                momentumRunning = false;
                return;
            }
            requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    function stopMomentum() {
        momentumRunning = false;
        momentumVX = 0;
        momentumVY = 0;
    }

    function distance(a, b) {
        var dx = a.x - b.x;
        var dy = a.y - b.y;
        return Math.hypot(dx, dy);
    }

    viewport.addEventListener('pointerdown', function (e) {
        viewport.setPointerCapture(e.pointerId);
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        stopMomentum();
        velocitySamples.length = 0;
        pushVelocity(e.clientX, e.clientY);

        if (pointers.size === 1) {
            lastSingleX = e.clientX;
            lastSingleY = e.clientY;
            dragMoved = 0;
            dragStartTime = performance.now();
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            dragTarget = e.target.closest('.canvas-cell');
            viewport.classList.add('dragging');
        } else if (pointers.size === 2) {
            var pts = Array.from(pointers.values());
            pinchStartDist = distance(pts[0], pts[1]);
            pinchStartScale = scale;
            var midX = (pts[0].x + pts[1].x) / 2;
            var midY = (pts[0].y + pts[1].y) / 2;
            pinchMidWorldX = (midX - offsetX) / scale;
            pinchMidWorldY = (midY - offsetY) / scale;
        }
    });

    viewport.addEventListener('pointermove', function (e) {
        if (!pointers.has(e.pointerId)) return;
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

        if (pointers.size === 1) {
            var dx = e.clientX - lastSingleX;
            var dy = e.clientY - lastSingleY;
            offsetX += dx;
            offsetY += dy;
            lastSingleX = e.clientX;
            lastSingleY = e.clientY;
            dragMoved += Math.hypot(dx, dy);
            pushVelocity(e.clientX, e.clientY);
            fadeHint();
            scheduleRender();
        } else if (pointers.size === 2) {
            var pts = Array.from(pointers.values());
            var dist = distance(pts[0], pts[1]);
            if (pinchStartDist > 0) {
                var newScale = clampScale(pinchStartScale * (dist / pinchStartDist));
                var midX = (pts[0].x + pts[1].x) / 2;
                var midY = (pts[0].y + pts[1].y) / 2;
                scale = newScale;
                offsetX = midX - pinchMidWorldX * scale;
                offsetY = midY - pinchMidWorldY * scale;
                dragMoved += 10;
                fadeHint();
                scheduleRender();
            }
        }
    });

    function endPointer(e) {
        if (!pointers.has(e.pointerId)) return;
        pointers.delete(e.pointerId);

        if (pointers.size === 0) {
            viewport.classList.remove('dragging');

            var elapsed = performance.now() - dragStartTime;
            var totalMove = Math.hypot(e.clientX - dragStartX, e.clientY - dragStartY);
            var isClick = totalMove < CLICK_MAX_MOVE && elapsed < CLICK_MAX_TIME && dragMoved < CLICK_MAX_MOVE;

            if (isClick && dragTarget && dragTarget.href) {
                window.open(dragTarget.href, '_blank', 'noopener');
            } else {
                var v = computeVelocity();
                if (Math.hypot(v.x, v.y) > MOMENTUM_STOP * 2) {
                    momentumVX = v.x;
                    momentumVY = v.y;
                    startMomentum();
                }
            }

            dragTarget = null;
            velocitySamples.length = 0;
        } else if (pointers.size === 1) {
            var remaining = Array.from(pointers.values())[0];
            lastSingleX = remaining.x;
            lastSingleY = remaining.y;
            pinchStartDist = 0;
        }
    }

    viewport.addEventListener('pointerup', endPointer);
    viewport.addEventListener('pointercancel', endPointer);

    // Suppress native anchor navigation — click is handled in endPointer.
    viewport.addEventListener('click', function (e) {
        var cell = e.target.closest('.canvas-cell');
        if (cell) e.preventDefault();
    });

    // ---- wheel: ctrlKey (pinch / ctrl+wheel) zooms; otherwise pans. ----
    viewport.addEventListener('wheel', function (e) {
        e.preventDefault();
        stopMomentum();

        if (e.ctrlKey) {
            var rect = viewport.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;
            var worldX = (mx - offsetX) / scale;
            var worldY = (my - offsetY) / scale;
            var factor = Math.exp(-e.deltaY * WHEEL_ZOOM_FACTOR);
            scale = clampScale(scale * factor);
            offsetX = mx - worldX * scale;
            offsetY = my - worldY * scale;
        } else {
            offsetX -= e.deltaX * WHEEL_PAN_FACTOR;
            offsetY -= e.deltaY * WHEEL_PAN_FACTOR;
        }
        fadeHint();
        scheduleRender();
    }, { passive: false });

    // ---- keyboard ----
    window.addEventListener('keydown', function (e) {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
        var step = e.shiftKey ? 200 : 60;
        var dx = 0, dy = 0;
        if (e.key === 'ArrowLeft') dx = step;
        else if (e.key === 'ArrowRight') dx = -step;
        else if (e.key === 'ArrowUp') dy = step;
        else if (e.key === 'ArrowDown') dy = -step;
        else if (e.key === '0') { scale = 1; offsetX = 0; offsetY = 0; centerInitial(); fadeHint(); scheduleRender(); e.preventDefault(); return; }
        else if (e.key === '+' || e.key === '=' || e.key === '-') {
            var rect = viewport.getBoundingClientRect();
            var cx = rect.width / 2, cy = rect.height / 2;
            var wx = (cx - offsetX) / scale;
            var wy = (cy - offsetY) / scale;
            scale = clampScale(scale * (e.key === '-' ? 0.85 : 1.15));
            offsetX = cx - wx * scale;
            offsetY = cy - wy * scale;
            fadeHint(); scheduleRender(); e.preventDefault(); return;
        }
        else return;
        e.preventDefault();
        stopMomentum();
        offsetX += dx;
        offsetY += dy;
        fadeHint();
        scheduleRender();
    });

    window.addEventListener('resize', scheduleRender);

    function centerInitial() {
        offsetX = viewport.clientWidth / 2 - 150;
        offsetY = viewport.clientHeight / 2 - ROW_H / 2;
    }

    centerInitial();
    scheduleRender();

    setTimeout(fadeHint, 6000);
})();
