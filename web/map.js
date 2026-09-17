(function () {
  "use strict";

  const DATA = window.__MAP_DATA__;
  if (!DATA) return;

  const app = document.querySelector(".map-app");
  const frame = document.querySelector(".map-frame");
  const svg = d3.select("#map-svg");
  const worldG = svg.append("g").attr("class", "world");
  const tooltip = document.querySelector(".tooltip");
  const searchInput = document.getElementById("search-input");
  const resetBtn = document.getElementById("reset-btn");
  const labelsOnBtn = document.getElementById("labels-on");
  const labelsOffBtn = document.getElementById("labels-off");
  const statEl = document.getElementById("stat-readout");
  const legendEl = document.getElementById("legend");
  const miniSvg = d3.select("#minimap-svg");
  const viewfinder = document.querySelector(".viewfinder");

  const points = DATA.points;
  const genreHue = DATA.genreHue;
  const hiddenGenres = new Set();

  statEl.textContent = `${points.length} styles · ${Object.keys(genreHue).length} genres`;

  const xExtent = d3.extent(points, (d) => d.dim0);
  const yExtent = d3.extent(points, (d) => d.dim1);

  // --- projection: fits the full (padded) data extent into a viewport at k=1,
  // centered. d3-zoom's transform (translate/scale) is layered on top of this
  // fixed base projection, never recomputed except when the frame resizes. ---
  function makeProjector(width, height, padding) {
    const dataW = (xExtent[1] - xExtent[0]) || 1;
    const dataH = (yExtent[1] - yExtent[0]) || 1;
    const availW = width * (1 - padding * 2);
    const availH = height * (1 - padding * 2);
    const scale = Math.min(availW / dataW, availH / dataH);
    const dcx = (xExtent[0] + xExtent[1]) / 2;
    const dcy = (yExtent[0] + yExtent[1]) / 2;
    const cx = width / 2;
    const cy = height / 2;
    return {
      scale,
      project: (dx, dy) => [cx + (dx - dcx) * scale, cy - (dy - dcy) * scale],
      invert: (px, py) => [dcx + (px - cx) / scale, dcy - (py - cy) / scale],
    };
  }

  let width = 0;
  let height = 0;
  let projector = null;
  let currentTransform = d3.zoomIdentity;

  const zoom = d3.zoom().scaleExtent([0.4, 60]).on("zoom", (event) => {
    currentTransform = event.transform;
    render();
  });

  svg.call(zoom).on("dblclick.zoom", null);
  svg.on("mousedown.cursor", () => frame.classList.add("is-dragging"));
  svg.on("mouseup.cursor mouseleave.cursor", () => frame.classList.remove("is-dragging"));

  const pointsSel = worldG
    .selectAll("g.point")
    .data(points)
    .join("g")
    .attr("class", "point")
    .attr("data-genre", (d) => d.genre)
    .on("mouseenter", (event, d) => showTooltip(event, d))
    .on("mousemove", (event) => moveTooltip(event))
    .on("mouseleave", hideTooltip)
    .on("click", (event, d) => {
      const url = `https://www.discogs.com/search?type=master&page=1&style_exact=${encodeURIComponent(d.style)}&sort=have%2Cdesc`;
      window.open(url, "_blank", "noopener");
    });

  pointsSel
    .append("circle")
    .attr("r", 5)
    .style("--hue", (d) => `${genreHue[d.genre] ?? 0}deg`)
    .style("fill", "hsl(var(--hue) var(--genre-sat) var(--genre-light))");

  pointsSel.append("text").text((d) => d.style);

  function render() {
    worldG.attr("transform", currentTransform);
    const k = currentTransform.k;
    pointsSel.attr("transform", (d) => `translate(${d.px},${d.py}) scale(${1 / k})`);
    updateMinimap();
  }

  function repositionPoints() {
    points.forEach((d) => {
      const [px, py] = projector.project(d.dim0, d.dim1);
      d.px = px;
      d.py = py;
    });
  }

  function zoomTo(px, py, k, animate) {
    const tx = width / 2 - k * px;
    const ty = height / 2 - k * py;
    const t = d3.zoomIdentity.translate(tx, ty).scale(k);
    const sel = animate ? svg.transition().duration(500) : svg;
    sel.call(zoom.transform, t);
  }

  function fitAll(animate) {
    zoomTo(width / 2, height / 2, 1, animate);
  }

  function resize(applyInitial) {
    const newWidth = frame.clientWidth;
    const newHeight = frame.clientHeight;
    if (!newWidth || !newHeight) return;

    // Capture the currently visible data-space window (center + zoom level)
    // under the OLD projector/transform before either changes, so a resize
    // (e.g. rotating a phone) keeps showing the same place instead of
    // stranding all points outside the new viewBox.
    let preserved = null;
    if (projector && !applyInitial) {
      const k = currentTransform.k;
      const centerData = projector.invert(
        (width / 2 - currentTransform.x) / k,
        (height / 2 - currentTransform.y) / k
      );
      preserved = { centerData, dataPerPixel: 1 / (projector.scale * k) };
    }

    width = newWidth;
    height = newHeight;
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    projector = makeProjector(width, height, 0.1);
    repositionPoints();

    if (applyInitial) {
      const focus = points.find((d) => d.style.toLowerCase() === DATA.init.style.toLowerCase());
      if (focus) {
        const k = Math.min(60, Math.max(0.4, 1 / DATA.init.marginPct));
        zoomTo(focus.px, focus.py, k, false);
        return;
      }
    }

    if (preserved) {
      const newK = Math.min(60, Math.max(0.4, 1 / (projector.scale * preserved.dataPerPixel)));
      const [wx, wy] = projector.project(preserved.centerData[0], preserved.centerData[1]);
      zoomTo(wx, wy, newK, false);
      return;
    }

    render();
  }

  // --- tooltip ---
  function showTooltip(event, d) {
    const hue = genreHue[d.genre] ?? 0;
    const rows = d.hover
      .map(
        ([genre, pct]) => `
        <div class="tooltip-row">
          <span>${genre.replace(/_/g, " ")}</span>
          <span class="pct">${(pct * 100).toFixed(0)}%</span>
        </div>
        <div class="tooltip-bar"><span style="width:${(pct * 100).toFixed(0)}%; background: hsl(${hue} var(--genre-sat) var(--genre-light))"></span></div>`
      )
      .join("");
    tooltip.innerHTML = `
      <div class="tooltip-title">
        <span class="tooltip-swatch" style="background: hsl(${hue} var(--genre-sat) var(--genre-light))"></span>
        ${d.style}
      </div>
      ${rows}`;
    tooltip.classList.add("is-visible");
    moveTooltip(event);
  }

  function moveTooltip(event) {
    const rect = frame.getBoundingClientRect();
    let left = event.clientX - rect.left + 14;
    let top = event.clientY - rect.top + 14;
    if (left + 240 > rect.width) left = event.clientX - rect.left - 254;
    if (top + 140 > rect.height) top = event.clientY - rect.top - 154;
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function hideTooltip() {
    tooltip.classList.remove("is-visible");
  }

  // --- search ---
  const normalize = (s) => (s || "").toLowerCase().replace(/[-_\s]+/g, "");

  function runSearch() {
    const term = normalize(searchInput.value);
    if (!term) return;
    const match = points.find((d) => normalize(d.style) === term);
    if (!match) {
      searchInput.classList.add("is-error");
      setTimeout(() => searchInput.classList.remove("is-error"), 900);
      return;
    }
    zoomTo(match.px, match.py, Math.max(currentTransform.k, 6), true);
    pulseRing(match);
  }

  function pulseRing(d) {
    svg.selectAll(".ring").remove();
    const ring = worldG
      .append("circle")
      .attr("class", "ring")
      .attr("cx", d.px)
      .attr("cy", d.py)
      .attr("r", 14);
    ring
      .transition()
      .duration(600)
      .attr("r", 26)
      .style("opacity", 0)
      .transition()
      .delay(200)
      .duration(600)
      .attr("r", 14)
      .style("opacity", 1)
      .on("end", function repeat() {
        d3.select(this)
          .transition()
          .duration(600)
          .attr("r", 26)
          .style("opacity", 0)
          .transition()
          .delay(200)
          .duration(600)
          .attr("r", 14)
          .style("opacity", 1)
          .on("end", repeat);
      });
    setTimeout(() => ring.remove(), 3200);
  }

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch();
  });

  resetBtn.addEventListener("click", () => fitAll(true));

  labelsOnBtn.addEventListener("click", () => setLabels(true));
  labelsOffBtn.addEventListener("click", () => setLabels(false));

  function setLabels(on) {
    app.classList.toggle("labels-off", !on);
    labelsOnBtn.classList.toggle("is-active", on);
    labelsOffBtn.classList.toggle("is-active", !on);
  }

  // --- legend ---
  const genreCounts = d3.rollup(points, (v) => v.length, (d) => d.genre);
  const genreList = Array.from(genreCounts, ([genre, count]) => ({ genre, count }))
    .sort((a, b) => b.count - a.count);

  genreList.forEach(({ genre, count }) => {
    const item = document.createElement("div");
    item.className = "legend-item";
    const hue = genreHue[genre] ?? 0;
    item.innerHTML = `
      <span class="legend-chip" style="background: hsl(${hue} var(--genre-sat) var(--genre-light))"></span>
      <span class="legend-name">${genre.replace(/_/g, " ")}</span>
      <span class="legend-count">${count}</span>`;
    item.addEventListener("click", () => {
      if (hiddenGenres.has(genre)) hiddenGenres.delete(genre);
      else hiddenGenres.add(genre);
      item.classList.toggle("is-off", hiddenGenres.has(genre));
      applyGenreFilter();
    });
    legendEl.appendChild(item);
  });

  function applyGenreFilter() {
    app.classList.toggle("genre-dim", hiddenGenres.size > 0);
    pointsSel.classed("is-dimmed", (d) => hiddenGenres.has(d.genre));
  }

  // --- minimap (static projection, redrawn once; only the viewfinder moves) ---
  let miniProjector = null;

  function buildMinimap() {
    const el = document.querySelector(".minimap");
    const mw = el.clientWidth;
    const mh = el.clientHeight;
    miniSvg.attr("viewBox", `0 0 ${mw} ${mh}`);
    miniProjector = makeProjector(mw, mh, 0.08);
    miniSvg
      .selectAll("circle")
      .data(points)
      .join("circle")
      .attr("cx", (d) => miniProjector.project(d.dim0, d.dim1)[0])
      .attr("cy", (d) => miniProjector.project(d.dim0, d.dim1)[1])
      .attr("r", 1.3)
      .style("--hue", (d) => `${genreHue[d.genre] ?? 0}deg`)
      .style("fill", "hsl(var(--hue) var(--genre-sat) var(--genre-light))")
      .style("opacity", 0.55);
  }

  function updateMinimap() {
    if (!miniProjector || !projector) return;
    const k = currentTransform.k;
    const tx = currentTransform.x;
    const ty = currentTransform.y;

    const c1 = projector.invert((0 - tx) / k, (0 - ty) / k);
    const c2 = projector.invert((width - tx) / k, (height - ty) / k);
    const dataX = [Math.min(c1[0], c2[0]), Math.max(c1[0], c2[0])];
    const dataY = [Math.min(c1[1], c2[1]), Math.max(c1[1], c2[1])];

    const m1 = miniProjector.project(dataX[0], dataY[0]);
    const m2 = miniProjector.project(dataX[1], dataY[1]);
    const el = document.querySelector(".minimap");
    const mw = el.clientWidth;
    const mh = el.clientHeight;

    const left = Math.max(0, Math.min(m1[0], m2[0]));
    const top = Math.max(0, Math.min(m1[1], m2[1]));
    const w = Math.min(mw, Math.abs(m2[0] - m1[0]));
    const h = Math.min(mh, Math.abs(m2[1] - m1[1]));

    viewfinder.style.left = `${left}px`;
    viewfinder.style.top = `${top}px`;
    viewfinder.style.width = `${w}px`;
    viewfinder.style.height = `${h}px`;
  }

  // --- boot ---
  buildMinimap();
  resize(true);

  const ro = new ResizeObserver(() => resize(false));
  ro.observe(frame);
  window.addEventListener("resize", () => buildMinimap());
})();
