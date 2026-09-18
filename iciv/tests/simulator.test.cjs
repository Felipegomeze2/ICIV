const {test} = require('node:test');
const assert = require('node:assert/strict');
const sim = require('../assets/simulator.cjs');

test('historical presets select one year, never dimension-wise maxima', () => {
  const dims = [{id:'a',weight:.6,hist:[90,20]}, {id:'b',weight:.4,hist:[10,100]}];
  const scores = [58,52];
  assert.deepEqual(sim.preset(dims,sim.historicalIndex(scores,'peak')), {a:90,b:10});
  assert.equal(sim.aggregate(dims,sim.preset(dims,0)),58);
  assert.equal(sim.aggregate(dims,sim.preset(dims,sim.historicalIndex(scores,'min'))),52);
});
test('missing dimensions remain missing and available weights renormalize', () => {
  const dims = [{id:'a',weight:.6,hist:[null]}, {id:'b',weight:.4,hist:[25]}];
  const values = sim.preset(dims,0);
  assert.deepEqual(values,{a:null,b:25});
  assert.equal(sim.aggregate(dims,values),25);
  assert.equal(sim.aggregate(dims,{a:null,b:null}),null);
  assert.equal(sim.aggregate(dims,{a:0,b:null}),0);
  assert.deepEqual(sim.preset(dims,-1),{a:null,b:null});
});
test('historical selection excludes non-finite data without treating null as zero', () => {
  assert.equal(sim.historicalIndex([null,40,0,NaN],'min'),2);
  assert.equal(sim.historicalIndex([null,40,0,Infinity],'peak'),1);
  assert.equal(sim.historicalIndex([null,NaN],'peak'),-1);
});
test('category thresholds match annual categories at decimal boundaries', () => {
  for (const [score,label] of [[0,'Muy desfavorable'],[30.99,'Muy desfavorable'],[31,'Desfavorable'],[50.99,'Desfavorable'],[51,'Intermedio'],[65.99,'Intermedio'],[66,'Favorable'],[80.99,'Favorable'],[81,'Muy favorable'],[100,'Muy favorable'],[null,'Sin datos']]) assert.equal(sim.category(score).label,label);
});
test('decimal dimension scores retain precision', () => {
  const dims = [{id:'a',weight:.5,hist:[87.93]}, {id:'b',weight:.5,hist:[81.67]}];
  assert.ok(Math.abs(sim.aggregate(dims,sim.preset(dims,0))-84.80)<1e-10);
});

test('dashboard payload reproduces every published annual score', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const html = fs.readFileSync(path.join(__dirname,'../../iciv_dashboard.html'),'utf8');
  const read = name => JSON.parse(html.match(new RegExp('const ' + name + '\\s*=\\s*(\\[[^;]+\\]);'))[1]);
  const dims = read('SIM_DIMS'), scores = read('SIM_HIST');
  scores.forEach((score,i) => {
    const calculated = sim.aggregate(dims,sim.preset(dims,i));
    if (score === null) assert.equal(calculated,null);
    else assert.ok(Math.abs(calculated-score) <= .005001, `Year index ${i}: ${calculated} versus ${score}`);
  });
  assert.match(html,/step="0\.01" aria-label=/);
});
