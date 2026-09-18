// Shared, dependency-free calculation rules for the standalone dashboard.
const ICIVSimulator = (() => {
  const valid = value => typeof value === 'number' && Number.isFinite(value);
  function aggregate(dims, values) {
    const available = dims.filter(d => valid(values[d.id]));
    const mass = available.reduce((s, d) => s + d.weight, 0);
    return mass > 0 ? available.reduce((s, d) => s + values[d.id] * d.weight, 0) / mass : null;
  }
  function historicalIndex(scores, mode) {
    let best = -1;
    scores.forEach((score, i) => {
      if (valid(score) && (best < 0 || (mode === 'peak' ? score > scores[best] : score < scores[best]))) best = i;
    });
    return best;
  }
  function preset(dims, index) {
    return Object.fromEntries(dims.map(d => [d.id, index < 0 || !valid(d.hist[index]) ? null : d.hist[index]]));
  }
  function category(s) {
    if (!valid(s)) return {label: 'Sin datos', color: '#686868'};
    if (s < 31) return {label: 'Muy desfavorable', color: '#9e2a2b'};
    if (s < 51) return {label: 'Desfavorable', color: '#c2600e'};
    if (s < 66) return {label: 'Intermedio', color: '#b07d00'};
    if (s < 81) return {label: 'Favorable', color: '#2f7d4f'};
    return {label: 'Muy favorable', color: '#1f6f78'};
  }
  return {valid, aggregate, historicalIndex, preset, category};
})();
if (typeof module !== 'undefined') module.exports = ICIVSimulator;
