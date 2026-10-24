/* Offline DOM tests of local source. No browser, network or pixel rendering. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..');
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'audit-v1.4/ui-fixtures.json')));
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(fs.readFileSync(path.join(root,'app/web/template.html'),'utf8'),{
 runScripts:'outside-only',url:'https://unit-test.invalid/',virtualConsole:vc
});
const w=dom.window;
w.HTMLElement.prototype.scrollIntoView=function(){};
w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
w.HTMLDialogElement.prototype.close=function(){this.open=false;};
w.fetch=()=>{throw Error('Network forbidden in offline DOM tests');};
w.FIXTURES=fixtures;
w.eval(['ui-core.js','laboratory.js','guided.js'].map(x=>fs.readFileSync(path.join(root,'app/web',x),'utf8')).join('\n')+`
 nativeMode=true;caps.xlsx=true;let current=null,currentLang='es';
 pyCall=async function(name,...args){
  if(name==='js_synthetic_catalog')return {ok:true,datasets:FIXTURES.catalog};
  if(name==='js_load_synthetic'){current=FIXTURES.examples[args[0]];return structuredClone(current.payload);}
  if(name==='js_run_init'){currentLang=JSON.parse(args[0]).lang;return {ok:true,vars:JSON.parse(args[0]).vars};}
  if(name==='js_run_var')return {ok:true,okv:true,clusters:[]};
  if(name==='js_run_done')return structuredClone(currentLang==='en'?current.done_en:current.done);
  if(name==='js_explain')return structuredClone(current.explain);
  if(name==='js_texts')return structuredClone(current.texts);
  if(name==='js_fig_panels')return {ok:true,panels:JSON.parse(args[0]).map(variable=>({variable,title:variable,svg:'',clusters:[],confirmed:false}))};
  if(name==='js_fig_detail'||name==='js_fig_pair')return {ok:true,png:''};
  if(name==='js_set_language'){currentLang=args[0];return {ok:true};}
  if(name==='js_set_varmap'||name==='js_update_style')return {ok:true};
  throw Error('Unmocked operation '+name);
 };
 window.unit={ready:()=>laboratoryReady(),cfg:()=>collectCfg(),upload:x=>{S.up=x;renderUpload(x);translateDOM();},translate:()=>translateDOM(),diagnostic:x=>translateDiagnostic(x),lang:x=>setLanguage(x),invalidate:()=>invalidateResults(),pending:x=>UPLOAD_PENDING=x,state:S};
`);
w.structuredClone=structuredClone;
(async()=>{
 await w.unit.ready();
 const $=s=>w.document.querySelector(s),$$=s=>[...w.document.querySelectorAll(s)];
 assert.equal($$('[data-load]').length,8);
 assert.equal($$('.example-actions a[download]').length,8);
 assert.equal($('#guidePanel').hidden,false);
 assert.equal(w.document.documentElement.lang,'en');
 assert.equal(w.unit.diagnostic('n insuficiente por grupo (mínimo 3).'),'Insufficient sample size per group (minimum 3).');
 assert.equal(w.unit.diagnostic('ID de sujeto obligatorio y no vacío / nonempty subject ID required.'),'nonempty subject ID required.');
 assert.equal($('#lang').value,'en');
 assert.equal($('[data-lang="en"]').classList.contains('on'),true);
 assert.match($('#datasetGallery').textContent,/Three conditions/);
 assert.doesNotMatch($('#datasetGallery').textContent,/Tres condiciones|Dos condiciones|Cargar ejemplo/);
 for(const spec of fixtures.catalog){
  await w.unit.lang('en');
  await $('[data-load="'+spec.key+'"]').onclick();
  assert.match($('#groupCounts').textContent,/n=30/);
  assert.equal(w.unit.state.p.n_subj,60);
  assert.equal(w.unit.cfg().probs.length,0);
  assert.equal(w.unit.cfg().cfg.design,spec.recipe.design);
  assert.equal(w.unit.cfg().cfg.group_filter,spec.recipe.group_filter||null);
  $('#guideNext').onclick();assert.equal($('#settingsDialog').open,true);
  await $('#btnRun').onclick();
  assert.equal($('#settingsDialog').open,false);
  assert.equal($('#interpretation').hidden,false);
  assert.equal($$('.explanation').length,spec.n_vars);
  assert.match($('#interpretation').textContent,/n=30/);
  assert.match($('#interpretation').textContent,/Synthetic data/);
  assert.equal(w.unit.cfg().cfg.lang,'en');
  if(spec.key==='08_acl_retest')assert.match($('#interpretation').textContent,/does not demonstrate equivalence/);
  await w.unit.lang('en');assert.match($('#interpretation').textContent,/Synthetic data/);
  assert.equal(w.document.documentElement.lang,'en');
  assert.match($('#datasetGallery').textContent,/30 cases/);assert.doesNotMatch($('#datasetGallery').textContent,/10 cases/);
  await w.unit.lang('es');assert.match($('#interpretation').textContent,/Datos sintéticos/);
  $('#alpha').value='0';assert.ok(w.unit.cfg().probs.length);$('#alpha').value='0.05';
  $('#alpha').dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.equal(w.unit.state.d,null);assert.equal($('#interpretation').hidden,true);
  w.unit.pending(true);assert.match(w.unit.cfg().probs.join(' '),/mapeo/);w.unit.pending(false);
  $('#vmBody select').dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.match(w.unit.cfg().probs.join(' '),/clasificación/);
  await $('#btnVm').onclick();assert.equal(w.unit.cfg().probs.length,0);
  $('#unitsConfirmed').checked=false;assert.ok(w.unit.cfg().probs.length);
 }
 await w.unit.lang('en');
 w.unit.upload({nrows:20,ncols:102,tipo:'csv',sep:',',decimal:'.',preview:{columns:['subject','Knee_0'],rows:[['001',1]]},structure:'wide',blocks:['Knee'],meta_cols:['subject'],columns:['subject','Knee_0'],numeric:['Knee_0']});
 assert.match($('#mapBox').textContent,/participant ID/);assert.doesNotMatch($('#mapBox').textContent,/Sujeto|El archivo|Aplicar mapeo/);
 $('#mSub').value='—';await $('#btnMap').onclick();assert.match($('#mapErr').textContent,/Select the participant ID column/);
 $('#modeLab').onclick();assert.equal($('#guidePanel').hidden,true);
 $('#modeGuided').onclick();assert.equal($('#guidePanel').hidden,false);
 w.unit.state.up={old:true};$('#upBox').hidden=false;
 await $('#file').onchange({target:{files:[{name:'failed.csv',arrayBuffer:async()=>new Uint8Array([1,2]).buffer}],value:'failed.csv'}});
 assert.equal(w.unit.state.p,null);assert.equal(w.unit.state.up,null);
 assert.equal($('#upBox').hidden,true);assert.equal($('#cfgBlk').hidden,true);
 assert.equal($('#errPanel').hidden,false);
 assert.match($('#errTxt').textContent,/Network forbidden/);
 assert.deepEqual(errors,[]);
 console.log('PASS: 8 guided example workflows, recipes, actual result fixtures, ES/EN, mode switch, invalidation and import guards. Offline DOM only.');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
