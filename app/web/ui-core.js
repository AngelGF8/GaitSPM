
'use strict';
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const PYVER='0.28.3', IDX='https://cdn.jsdelivr.net/pyodide/v'+PYVER+'/full/';
const DESIGNS={ttest2:'Comparar 2 grupos independientes (SPM{t})',paired_cond:'Comparar 2 condiciones pareadas, p. ej. pre-post (SPM{t})',paired_side:'Comparar lados I vs D, pareado (SPM{t})',anova1:'Comparar ≥3 grupos independientes (SPM{F})',anova1rm:'Comparar ≥3 condiciones intra-sujeto, RM-ANOVA (SPM{F})',regress:'Asociación con covariable continua, regresión (SPM{t})'};
const JES={pelvis:'Pelvis',hip:'Cadera',knee:'Rodilla',ankle:'Tobillo'};
const PES={sagittal:'Sagital',frontal:'Frontal',transverse:'Transversal'};
const GUESS={sub:['sujet','subject','id','part'],grp:['grupo','group'],con:['cond','sesion','session','visit','momento'],sid:['lado','side','limb','pierna'],nod:['punto','node','point','frame','cycle','perc','%'],val:['valor','value','angle','ang','deg'],vrb:['variable','var','param','output','señal','signal'],tri:['trial','ensayo','rep']};
let py=null; let nativeMode=false; let SESSION=Array.from(crypto.getRandomValues(new Uint8Array(24)),b=>b.toString(16).padStart(2,'0')).join(''); const caps={xlsx:false};
const S={p:null,up:null,d:null,cfg:null,tx:null,title:'',fname:''};
const STYLE_COLORS=['#0072bd','#d95319','#edb120','#7e2f8e','#77ac30','#4dbeee','#a2142f'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function b64u8(b){const s=atob(b),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return u;}
function dl(b64,mime,fname){const blob=new Blob([b64u8(b64)],{type:mime});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=fname;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);}
function esc(t){return String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function showErr(src,o){$('#errTxt').textContent=T(src)+': '+translateDiagnostic(o.error||'')+(o.trace?'\n\n'+o.trace:'');$('#errPanel').hidden=false;}
$('#errClose').onclick=()=>{$('#errPanel').hidden=true;};
$('#errCopy').onclick=()=>{try{navigator.clipboard.writeText($('#errTxt').textContent);}catch(e){}};
async function pyCall(name){const args=Array.prototype.slice.call(arguments,1);await sleep(12);
 if(nativeMode){ const rr=await fetch("/api/call", {method:"POST",headers:{"Content-Type":"application/json","X-GaitSPM-Session":SESSION},body:JSON.stringify({name,args})}); const o=await rr.json(); if(!o.ok){showErr(name,o);throw new Error(o.error||name);} return o; }
 const f=py.globals.get(name);let s;try{s=f.apply(null,args);}finally{if(f&&f.destroy)f.destroy();}
 let o;try{o=JSON.parse(s);}catch(e){o={ok:false,error:'Respuesta no válida de '+name,trace:String(s).slice(0,1200)};}
 if(!o.ok){showErr(name,o);throw new Error(o.error||name);}return o;}

/* ---------- arranque ---------- */
function setBoot(p,msg){$('#bootFill').style.width=p+'%';if(msg)$('#bootMsg').textContent=T(msg);}
function bootTail(m){const t=String(m).trim();if(!t)return;const el=$('#bootLog');el.textContent=(el.textContent+'\n'+t).split('\n').slice(-6).join('\n');el.scrollTop=1e9;}
async function boot(){try{
 translateDOM();
 if(location.protocol.startsWith('http')) {try { const rr=await fetch('/api/ping'); const p=await rr.json(); nativeMode=p.ok===true; } catch(e){} }
 if(nativeMode){caps.xlsx=true; const p=await pyCall('js_ping'); $('#envChip').textContent='spm1d '+p.spm1d+' · Python local · '+p.engine; $('#boot').remove(); $('#app').hidden=false; await laboratoryReady(); return;}
 if(typeof loadPyodide==='undefined') await new Promise((resolve,reject)=>{const sc=document.createElement('script');sc.src=IDX+'pyodide.js';sc.onload=resolve;sc.onerror=()=>reject(new Error('Pyodide download failed. Use Python local mode or connect to the internet.'));document.head.append(sc);});
 setBoot(4,'Cargando runtime de Python (WebAssembly)…');await sleep(30);
 py=await loadPyodide({indexURL:IDX});
 setBoot(20,'Instalando NumPy · SciPy · Pandas · Matplotlib…');
 await py.loadPackage(['numpy','scipy','pandas','matplotlib'],{messageCallback:bootTail,errorCallback:bootTail});
 setBoot(60,'Complemento openpyxl (exportación XLSX)…');
 try{const xb=document.getElementById('xlsx-zip').textContent.trim();py.FS.writeFile('/xlsx.zip',b64u8(xb));py.runPython("import zipfile,sys\nzipfile.ZipFile('/xlsx.zip').extractall('/vendor')\nsys.path.insert(0,'/vendor')\nimport openpyxl");caps.xlsx=true;}catch(e){caps.xlsx=false;bootTail('XLSX unavailable: '+e.message);}
 setBoot(70,'Instalando spm1d (vendorizado)…');await sleep(20);
 const zb=document.getElementById('spm1d-zip').textContent.replace(/[^A-Za-z0-9+/=]/g,'');
 py.FS.writeFile('/spm1d_min.zip',b64u8(zb));
 py.runPython("import zipfile,sys\nzipfile.ZipFile('/spm1d_min.zip').extractall('/vendor')\nsys.path.insert(0,'/vendor')");
 setBoot(78,'Compilando motor GaitSPM…');await sleep(20);
 py.runPython("import matplotlib\nmatplotlib.use('Agg')");
 py.runPython(document.getElementById('py-engine').textContent);
 setBoot(92,'Puente JS ↔ Python…');await sleep(20);
 py.runPython(document.getElementById('py-simulation').textContent);
 py.runPython(document.getElementById('py-bridge').textContent);
 const ping=JSON.parse(py.globals.get('js_ping')());
 $('#envChip').textContent='spm1d '+ping.spm1d+' · motor '+ping.engine+(caps.xlsx?' · XLSX ✓':' · solo CSV');
 setBoot(100,'Listo');await sleep(300);
 const b=$('#boot');if(b)b.remove();$('#app').hidden=false; await laboratoryReady();
}catch(e){const eb=$('#bootErr');eb.hidden=false;eb.textContent='Unable to start: '+((e&&e.message)?e.message:e)+'\n\nSuggestions:\n· Use the Python launcher for local mode.\n· Browser-only mode needs internet for its first runtime download.\n· Reload with Ctrl+F5.\n· Use a current Chrome, Edge or Firefox.\n· Open the console (F12) and copy the error if it persists.';console.error(e);}}

/* ---------- utilidades de datos ---------- */
function varLabel(v){const r=((S.p&&S.p.varmap)||[]).find(x=>x.variable===v)||{};return (JES[r.joint]||'—')+'·'+(PES[r.plane]||'—')+' — '+v;}
function afterLoad(p,srcName){S.p=p;S.d=null;S.tx=null;
 const dc=$('#dataChip');dc.hidden=false;
 dc.textContent=srcName+' · '+p.n_subj+' sujetos · '+(p.groups.length||'—')+' grupos · '+p.conds.length+' cond · '+p.all_vars.length+' variables · '+p.n_curves+' curvas';
 renderCanon();buildCfg();$('#cfgBlk').hidden=false;
 $('#infBox').hidden=true;$('#infEmpty').hidden=false;
 $('#detBox').hidden=true;$('#detEmpty').hidden=false;
 $('#txtBox').hidden=true;$('#txtEmpty').hidden=false;
 goTab('datos');if(typeof dataChanged==='function')dataChanged(srcName);}
function renderCanon(){const p=S.p;$('#datosEmpty').hidden=true;$('#canonBox').hidden=false;
 const q=p.quality||{},M=[['Sujetos',p.n_subj],['Curvas',p.n_curves],['Variables',p.all_vars.length],['Completitud',(q.completeness_pct===undefined?'—':q.completeness_pct.toFixed(1)+' %')]];
 $('#cMetrics').innerHTML=M.map(x=>'<div class="metric"><b>'+x[1]+'</b><span>'+x[0]+'</span></div>').join('');
 const collisions=q.subject_group_collisions||[];
 $('#cQuality').innerHTML=collisions.length?'<b>Revisar IDs:</b> aparecen en varios grupos: '+esc(collisions.slice(0,8).join(', ')):
  (q.incomplete_curves?'<b>Revisar cobertura:</b> '+q.incomplete_curves+' curvas no contienen los 101 nodos completos.':'<b>Control de calidad listo.</b> Identificadores, nodos 0–100 y estructura canónica preparados.');
 const jo=[['','—'],['pelvis','Pelvis'],['hip','Cadera'],['knee','Rodilla'],['ankle','Tobillo']];
 const po=[['','—'],['sagittal','Sagital'],['frontal','Frontal'],['transverse','Transversal']];
 const opts=(arr,sel)=>arr.map(a=>'<option value="'+a[0]+'"'+(a[0]===sel?' selected':'')+'>'+a[1]+'</option>').join('');
 $('#vmBody').innerHTML=p.varmap.map((r,i)=>'<tr><td>'+esc(r.variable)+'</td><td><select data-i="'+i+'" data-k="joint">'+opts(jo,r.joint)+'</select></td><td><select data-i="'+i+'" data-k="plane">'+opts(po,r.plane)+'</select></td></tr>').join('');
 $('#vmBody').onchange=e=>{const t=e.target;if(t.tagName!=='SELECT')return;S.p.varmap[+t.dataset.i][t.dataset.k]=t.value;$('#btnVm').disabled=false;};
 $('#btnVm').disabled=true;
 $('#covHint').textContent='Covariables numéricas: '+((p.covs&&p.covs.length)?p.covs.join(', '):'ninguna');}
$('#btnVm').onclick=async()=>{await pyCall('js_set_varmap',JSON.stringify(S.p.varmap));$('#btnVm').disabled=true;buildVars();};

/* ---------- configuración de análisis ---------- */
function buildCfg(){const p=S.p,ds=$('#design');
 ds.innerHTML=Object.keys(DESIGNS).map(k=>'<option value="'+k+'">'+esc(DESIGNS[k])+'</option>').join('');
 ds.onchange=renderDyn;
 $('#band').innerHTML='<option value="">(ninguna)</option>'+p.groups.map(g=>'<option'+(g==='Control'?' selected':'')+'>'+esc(g)+'</option>').join('');
 buildVars();renderDyn();
 $('#mode').onchange=()=>{const m=$('#mode').value,isNp=m!=='param';
  $('#iterWrap').hidden=!isNp;$('#seedWrap').hidden=!isNp;$('#autoWrap').hidden=m!=='auto';};$('#mode').onchange();}
function buildVars(){const p=S.p,box=$('#varsBox');
 const order=v=>{const r=p.varmap.find(x=>x.variable===v)||{};const jo={pelvis:0,hip:1,knee:2,ankle:3},po={sagittal:0,frontal:1,transverse:2};
  return ((jo[r.joint]!==undefined?jo[r.joint]:9)*10)+(po[r.plane]!==undefined?po[r.plane]:9);};
 const vs=p.all_vars.slice().sort((a,b)=>order(a)-order(b)||a.localeCompare(b));
 box.innerHTML=vs.map(v=>{const r=p.varmap.find(x=>x.variable===v)||{};const on=r.joint&&r.plane;
  return '<label class="chk"><input type="checkbox" value="'+esc(v)+'"'+(on?' checked':'')+'>'+esc(varLabel(v))+'</label>';}).join('');}
function styleLabels(){const p=S.p||{groups:[],conds:[]},d=$('#design').value;
 if(d==='ttest2'||d==='anova1'){const selected=checks('gChecks');return selected.length?selected:p.groups.slice(0,d==='ttest2'?2:3);}
 if(d==='paired_cond')return [$('#pcA')?$('#pcA').value:'A',$('#pcB')?$('#pcB').value:'B'];
 if(d==='anova1rm'){const selected=checks('rmChecks');return selected.length?selected:p.conds;}
 if(d==='paired_side')return ['L','R'];
 return ['Media de regresión'];}
function renderStyleColors(){const box=$('#lineColors');if(!box)return;
 const labels=styleLabels().slice(0,STYLE_COLORS.length);
 box.innerHTML=labels.map((label,i)=>'<label class="colorrow">'+esc(label)+'<input type="color" data-style-i="'+i+'" value="'+STYLE_COLORS[i]+'"></label>').join('');
 box.querySelectorAll('input').forEach(el=>{el.oninput=()=>{STYLE_COLORS[+el.dataset.styleI]=el.value;};});}
function collectStyle(){return {
 line_colors:STYLE_COLORS.slice(),reference_band_color:$('#referenceColor').value,
 interval_mode:$('#intervalMode').value,interval_alpha:parseFloat($('#intervalAlpha').value),
 show_interval_edges:$('#intervalEdges').checked,cluster_fill_color:$('#clusterColor').value,
 cluster_fill_alpha:parseFloat($('#clusterAlpha').value),show_cluster_bars:$('#clusterBars').checked};}
function renderDyn(){const p=S.p,d=$('#design').value,H=[];
 const so=a=>a.map(x=>'<option>'+esc(x)+'</option>').join('');
 if(d==='ttest2'||d==='anova1'){const k=(d==='ttest2')?2:3,preferred=(d==='ttest2'&&p.groups.includes('Control')&&p.groups.includes('FAI cam'))?['Control','FAI cam']:p.groups.slice(0,k);
  H.push('<div class="fld">Grupos '+(d==='ttest2'?'(elige 2)':'(mínimo 3)')+'<div id="gChecks" class="checks">'+p.groups.map(g=>'<label class="chk"><input type="checkbox" value="'+esc(g)+'"'+(preferred.includes(g)?' checked':'')+'>'+esc(g)+'</label>').join('')+'</div></div>');}
 if(d==='paired_cond')H.push('<div class="fld two"><label>Nivel A<select id="pcA">'+so(p.conds)+'</select></label><label>Nivel B<select id="pcB">'+so(p.conds)+'</select></label></div>');
 if(d==='anova1rm')H.push('<div class="fld">Condiciones (mínimo 3)<div id="rmChecks" class="checks">'+p.conds.map(c=>'<label class="chk"><input type="checkbox" value="'+esc(c)+'" checked>'+esc(c)+'</label>').join('')+'</div></div>');
 if(d==='regress')H.push('<label class="fld">Covariable<select id="covSel">'+(p.covs.length?so(p.covs):'<option value="">— sin covariables numéricas —</option>')+'</select></label>');
 if((d==='ttest2'||d==='anova1'||d==='regress'||d==='paired_side')&&p.conds.length>1)H.push('<label class="fld">Condición analizada<select id="condSel">'+so(p.conds)+'</select></label>');
 if((d==='paired_cond'||d==='paired_side'||d==='anova1rm'||d==='regress')&&p.groups.length)H.push('<label class="fld">Filtrar grupo<select id="gFilt"><option value="">(todos)</option>'+so(p.groups)+'</select></label>');
 if(p.sides.length&&d!=='paired_side'){
  H.push('<label class="fld">Lados<select id="sideMode"><option value="mean">Promediar L y R</option><option value="L">Solo L</option><option value="R">Solo R</option></select><small class="mut">Cada sujeto aporta una observación; no se permite pseudo-replicación L/R.</small></label>');}
 if(d==='paired_side')H.push('<p class="hint">Comparación pareada L vs R'+((p.sides.indexOf('L')>=0&&p.sides.indexOf('R')>=0)?'':' — <b>los datos no incluyen ambos lados</b>')+'.</p>');
 $('#dyn').innerHTML=H.join('');
 if($('#pcB')&&p.conds.length>1)$('#pcB').selectedIndex=1;
 const isT=(d==='ttest2'||d==='paired_cond'||d==='paired_side'||d==='regress');
 $('#ttWrap').hidden=!isT;$('#evWrap').hidden=!(d==='ttest2'||d==='anova1');
 $('#phWrap').hidden=!(d==='anova1'||d==='anova1rm');
 $('#dyn').onchange=renderStyleColors;renderStyleColors();}
function checks(id){const el=$('#'+id);return el?Array.from(el.querySelectorAll('input:checked')).map(i=>i.value):[];}
function collectCfg(){const p=S.p,d=$('#design').value,probs=[]; if(!p)return {cfg:{},probs:['Carga datos primero / Load data first.']};
 const cfg={design:d,alpha:Number($('#alpha').value),
  two_tailed:(!$('#ttWrap').hidden)&&$('#twoTailed').checked,
  mode:$('#mode').value,iterations:parseInt($('#iters').value)||5000,
  seed:(()=>{const v=parseInt($('#seed').value);return Number.isFinite(v)?v:2026;})(),
  auto_normality_cutoff:parseFloat($('#autoCut').value)||20,
  field_correction:$('#fieldCorrection').value,
  equal_var:$('#evWrap').hidden?true:$('#equalVar').checked,
  posthoc:$('#phWrap').hidden?false:$('#posthoc').checked,
  side_mode:'mean',band_group:$('#band').value||null,band_k:parseInt($('#bandK').value)||1,
  lang:$('#lang').value,vars:checks('varsBox'),
  groups:null,cond:null,cond_levels:null,side_levels:null,group_filter:null,covariate:null};
 Object.assign(cfg,collectStyle());
 if(d==='ttest2'){cfg.groups=checks('gChecks');if(cfg.groups.length!==2)probs.push('Selecciona exactamente 2 grupos.');}
 if(d==='anova1'){cfg.groups=checks('gChecks');if(cfg.groups.length<3)probs.push('Selecciona al menos 3 grupos.');}
 if(d==='paired_cond'){if(p.conds.length<2)probs.push('Se necesitan al menos 2 condiciones en los datos.');
  else{cfg.cond_levels=[$('#pcA').value,$('#pcB').value];if(cfg.cond_levels[0]===cfg.cond_levels[1])probs.push('Los dos niveles deben ser distintos.');}}
 if(d==='anova1rm'){cfg.cond_levels=checks('rmChecks');if(cfg.cond_levels.length<3)probs.push('Selecciona al menos 3 condiciones.');}
 if(d==='paired_side'){if(!(p.sides.indexOf('L')>=0&&p.sides.indexOf('R')>=0))probs.push('Se necesitan lados L y R en los datos.');cfg.side_levels=['L','R'];}
 if(d==='regress'){cfg.covariate=$('#covSel')?$('#covSel').value:'';if(!cfg.covariate)probs.push('No hay covariable numérica disponible.');}
 if($('#condSel'))cfg.cond=$('#condSel').value;
 if($('#gFilt'))cfg.group_filter=$('#gFilt').value||null;
 if($('#sideMode'))cfg.side_mode=$('#sideMode').value;
 if(!Number.isFinite(cfg.alpha)||cfg.alpha<=0||cfg.alpha>=1)probs.push('α debe estar entre 0 y 1 / alpha must lie between 0 and 1.');
 if(!cfg.vars.length)probs.push('Selecciona al menos una variable.');
 const slots={};p.varmap.filter(r=>cfg.vars.includes(r.variable)&&r.joint&&r.plane).forEach(r=>{
  const k=r.joint+'|'+r.plane;(slots[k]||(slots[k]=[])).push(r.variable);});
 Object.values(slots).filter(v=>v.length>1).forEach(v=>probs.push('Variables duplicadas en una articulación/plano: '+v.join(', ')+'.'));
 const collisions=(p.quality&&p.quality.subject_group_collisions)||[];
 if(collisions.length)probs.push('Un mismo ID aparece en varios grupos: '+collisions.slice(0,8).join(', ')+'.');
 return {cfg:cfg,probs:probs.map(translateString)};}

/* ---------- ejecución ---------- */
function setRun(p,msg){$('#runFill').style.width=p+'%';$('#runMsg').textContent=msg;}
$('#btnRun').onclick=async()=>{const r=collectCfg(),eb=$('#cfgErr');
 if(r.probs.length){eb.hidden=false;eb.innerHTML=r.probs.map(esc).join('<br>');return;}
 eb.hidden=true;const btn=$('#btnRun');btn.disabled=true;$('#runWrap').hidden=false;$('#runLog').textContent='';
 try{
  const init=await pyCall('js_run_init',JSON.stringify(r.cfg));const vars=init.vars,n=Math.max(vars.length,1);
  for(let i=0;i<vars.length;i++){const v=vars[i];
   setRun(Math.round(94*i/n),'Analizando '+v+' ('+(i+1)+'/'+n+')…');
   const rv=await pyCall('js_run_var',v);
   const line=rv.okv?(rv.clusters.length?('● '+rv.clusters.map(c=>c.x0+'–'+c.x1+'% '+c.p).join(' · ')):'○ n.s.'):('⚠ '+rv.error);
   $('#runLog').textContent+=v+'  '+line+'\n';$('#runLog').scrollTop=1e9;}
  setRun(96,'Componiendo tabla y textos…');
  const d=await pyCall('js_run_done');S.d=d;S.cfg=r.cfg;
  S.title='GaitSPM · '+T(DESIGNS[r.cfg.design]).split(' (')[0]+' · α = '+r.cfg.alpha;
  const corr=d.correction==='bonferroni'?'Bonferroni α/m':'sin ajuste';
  $('#sigChip').textContent=d.nsig+'/'+d.ntot+' confirmadas · '+corr;
  await renderInforme();await fillDetalle();await fillTextos();
  setRun(100,'Hecho');goTab('informe');$('#settingsDialog').close();updateRibbon();
 }catch(e){console.error(e);}
 finally{btn.disabled=false;setTimeout(()=>{$('#runWrap').hidden=true;},1200);}};

/* ---------- informe ---------- */
async function refreshRepImg(){ await refreshLabPanels(); }
async function renderInforme(){const d=S.d;if(!d)return;
 $('#infEmpty').hidden=true;$('#infBox').hidden=false;
 await refreshRepImg();
 const t=d.table,ci=t.columns.findIndex(c=>['Confirmado','Confirmed'].includes(c));
 $('#tabWrap').innerHTML='<table><thead><tr>'+t.columns.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+
  t.rows.map(rw=>'<tr'+((ci>=0&&['Sí','Yes'].includes(rw[ci]))?' class="sig"':'')+'>'+rw.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
 const wl=d.warnings||[],el2=d.errors||[],wb=$('#warnBox');
 if(wl.length||el2.length){wb.hidden=false;wb.querySelector('summary').textContent='⚠ Avisos ('+wl.length+') y errores ('+el2.length+')';
  $('#warnList').innerHTML=el2.map(x=>'<div class="w err">'+esc(translateDiagnostic(x))+'</div>').join('')+wl.map(x=>'<div class="w">'+esc(translateDiagnostic(x))+'</div>').join('');}
 else wb.hidden=true;
 $('#dlXlsx').disabled=!caps.xlsx;$('#dlXlsx').title=caps.xlsx?'':'openpyxl no disponible en esta carga';}
$('#incSpm').onchange=()=>{if(S.d)refreshRepImg();};
$('#btnStyleApply').onclick=async()=>{const b=$('#btnStyleApply');
 if(!S.d){b.textContent='Ejecuta primero un análisis';setTimeout(()=>{b.textContent='Aplicar al informe';},1600);return;}
 b.disabled=true;b.textContent='Aplicando…';
 try{const style=collectStyle();await pyCall('js_update_style',JSON.stringify(style));
  Object.assign(S.cfg,style);await refreshRepImg();
  if(!$('#detBox').hidden&&$('#detVar').value)await showDetail($('#detVar').value);
  await fillTextos();b.textContent='Aplicado ✓';}
 finally{setTimeout(()=>{b.disabled=false;b.textContent='Aplicar al informe';},1100);}};
async function exportRep(fmt,dpi){const e=await pyCall('js_export_report',fmt,dpi,$('#incSpm').checked,S.title);dl(e.b64,e.mime,e.fname);}
$('#dlPng3').onclick=()=>exportRep('png',300);
$('#dlPng6').onclick=()=>exportRep('png',600);
$('#dlSvg').onclick=()=>exportRep('svg',300);
$('#dlPdf').onclick=()=>exportRep('pdf',300);
$('#dlCsv').onclick=async()=>{const e=await pyCall('js_table_csv');dl(e.b64,e.mime,e.fname);};
$('#dlXlsx').onclick=async()=>{const e=await pyCall('js_table_xlsx');dl(e.b64,e.mime,e.fname);};

/* ---------- detalle ---------- */
async function fillDetalle(){const d=S.d;
 if(!d.okVars.length){$('#detEmpty').hidden=false;$('#detBox').hidden=true;return;}
 $('#detEmpty').hidden=true;$('#detBox').hidden=false;
 $('#detVar').innerHTML=d.okVars.map(v=>'<option value="'+esc(v)+'">'+esc(varLabel(v))+'</option>').join('');
 $('#detVar').onchange=()=>showDetail($('#detVar').value);
 await showDetail(d.okVars[0]);}
async function showDetail(v){const info=S.d.detail[v]||{};
 const corr=info.field_correction==='bonferroni'?'Bonferroni α/m':'sin ajuste';
 const chips=['Modo: '+(info.mode==='param'?'Paramétrico (RFT)':'SnPM'),'Umbral: '+info.stat+'* = '+info.zstar,(info.df||'—'),'Normalidad: '+((info.norm===null||info.norm===undefined)?'—':info.norm+' % nodos p<.05'),'min p cluster ('+corr+'): '+(info.field_p_adj===0?'<0.0001':info.field_p_adj),(info.confirmed?'Resultado confirmado':'No confirmado tras ajuste')];
 $('#detChips').innerHTML=chips.map(x=>'<span class="chip">'+esc(x)+'</span>').join('');
 const img=$('#detImg');img.classList.add('busy');
 const fd=await pyCall('js_fig_detail',v,110);img.src='data:image/png;base64,'+fd.png;img.classList.remove('busy');
 const labs=S.d.posthoc[v]||[],pb=$('#phBox');
 if(labs.length){pb.hidden=false;$('#phSel').innerHTML=labs.map(l=>'<option>'+esc(l)+'</option>').join('');
  $('#phSel').onchange=()=>showPair(v,$('#phSel').value);showPair(v,labs[0]);}
 else pb.hidden=true;
 $('#dlDet6').onclick=async()=>{const e=await pyCall('js_export_detail',v,'png',600);dl(e.b64,e.mime,e.fname);};
 $('#dlDetSvg').onclick=async()=>{const e=await pyCall('js_export_detail',v,'svg',300);dl(e.b64,e.mime,e.fname);};}
async function showPair(v,l){const img=$('#phImg');img.classList.add('busy');
 const fp=await pyCall('js_fig_pair',v,l,110);img.src='data:image/png;base64,'+fp.png;img.classList.remove('busy');}

/* ---------- textos ---------- */
async function fillTextos(){const tx=await pyCall('js_texts');S.tx=tx;
 $('#txtEmpty').hidden=true;$('#txtBox').hidden=false;
 for(const id of ['mtEs','rtEs'])$('#'+id).closest('.box').hidden=LANG==='en';
 for(const id of ['mtEn','rtEn'])$('#'+id).closest('.box').hidden=LANG==='es';
 $('#mtEs').value=tx.mt_es;$('#mtEn').value=tx.mt_en;$('#rtEs').value=tx.rt_es;$('#rtEn').value=tx.rt_en;
 $('#refs').innerHTML=tx.citas.map(c=>'<li>'+esc(c)+'</li>').join('');}
$('#btnTxt').onclick=()=>{const t=S.tx;if(!t)return;
 const s=LANG==='en'?'METHODS\n'+t.mt_en+'\n\nRESULTS\n'+t.rt_en+'\n':'MÉTODOS\n'+t.mt_es+'\n\nRESULTADOS\n'+t.rt_es+'\n';
 dl(btoa(unescape(encodeURIComponent(s))),'text/plain','gaitspm_textos.txt');};
$$('.copybtn').forEach(b=>{b.onclick=()=>{const ta=$(b.dataset.for);ta.select();
 try{if(navigator.clipboard)navigator.clipboard.writeText(ta.value);else document.execCommand('copy');}catch(e){}
 b.textContent='Copiado ✓';setTimeout(()=>{b.textContent='Copiar';},1200);};});

/* ---------- datos: demo, plantillas, subida ---------- */
$('#btnDemo').onclick=async()=>{const b=$('#btnDemo');b.disabled=true;const t0=b.textContent;b.textContent='Generando demo…';
 try{const p=await pyCall('js_load_demo',12);afterLoad(p,'Demo FAI');}catch(e){}finally{b.disabled=false;b.textContent=t0;}};
$('#btnTpl').onclick=async()=>{const t=await pyCall('js_templates');
 dl(t.wide,'text/csv','plantilla_marcha_ancho.csv');await sleep(300);dl(t.long,'text/csv','plantilla_marcha_largo.csv');};
$('#file').onchange=async e=>{const f=e.target.files[0];if(!f)return;S.fname=f.name;
 try{const buf=new Uint8Array(await f.arrayBuffer());if(nativeMode){const r=await fetch('/api/upload',{method:'POST',headers:{'X-GaitSPM-Session':SESSION},body:buf});if(!r.ok)throw new Error('Upload failed');}else py.FS.writeFile('/upload.bin',buf);
  const up=await pyCall('js_parse_upload',f.name,'');S.up=up;renderUpload(up);goTab('datos');}catch(err){showErr('Carga / Upload',{error:err.message||String(err)});}
 e.target.value='';};
function renderUpload(up){$('#datosEmpty').hidden=true;$('#upBox').hidden=false;$('#mapErr').hidden=true;
 $('#upInfo').textContent=S.fname+' — '+up.nrows+' filas × '+up.ncols+' columnas · '+
  (up.tipo==='csv'?('sep «'+up.sep+'» · decimal «'+up.decimal+'»'):('hoja «'+(up.hoja||'')+'»'));
 const sw=$('#sheetWrap');
 if(up.hojas&&up.hojas.length>1){sw.hidden=false;
  $('#sheetSel').innerHTML=up.hojas.map(h=>'<option'+(h===String(up.hoja)?' selected':'')+'>'+esc(h)+'</option>').join('');
  $('#sheetSel').onchange=async()=>{const u2=await pyCall('js_parse_upload',S.fname,$('#sheetSel').value);S.up=u2;renderUpload(u2);};}
 else sw.hidden=true;
 const pv=up.preview,K=14;
 $('#prevWrap').innerHTML='<table><thead><tr>'+pv.columns.slice(0,K).map(c=>'<th>'+esc(c)+'</th>').join('')+(pv.columns.length>K?'<th>…</th>':'')+'</tr></thead><tbody>'+
  pv.rows.map(rw=>'<tr>'+rw.slice(0,K).map(c=>'<td>'+esc(String(c).slice(0,18))+'</td>').join('')+(rw.length>K?'<td>…</td>':'')+'</tr>').join('')+'</tbody></table>';
 const lbl={wide:'Ancho · bloques Variable_0…100',long:'Largo · una fila por punto',transposed:'Transpuesto · filas 0–100'};
 const def=(up.structure==='unknown')?'wide':up.structure;
 $('#stRadios').innerHTML=['wide','long','transposed'].map(s=>'<label class="chk"><input type="radio" name="est" value="'+s+'"'+(s===def?' checked':'')+'>'+lbl[s]+'</label>').join('');
 $('#stHint').hidden=(up.structure!=='unknown');
 $('#stRadios').onchange=renderMap;renderMap();}
function mapErr(m){const e=$('#mapErr');if(m){e.hidden=false;e.textContent=translateString(m);}else e.hidden=true;}
function guessSel(opts,keys){for(let i=0;i<keys.length;i++){for(let j=0;j<opts.length;j++){const c=opts[j];
 if(c!=='—'&&String(c).toLowerCase().indexOf(keys[i])>=0)return c;}}return '—';}
function selHtml(id,label,opts,def,req){return '<label class="fld">'+label+(req?' *':'')+'<select id="'+id+'">'+
 opts.map(o=>'<option'+(o===def?' selected':'')+'>'+esc(o)+'</option>').join('')+'</select></label>';}
function v(id){const el=$('#'+id);return el?el.value:'';}
function renderMap(){const up=S.up;if(!up)return;mapErr(null);
 const est=(document.querySelector('input[name=est]:checked')||{value:'wide'}).value,mb=$('#mapBox'),H=[];
 if(est==='wide'){
  if(!up.blocks.length){mb.innerHTML='<div class="errbox">No encuentro bloques Variable_0…100. Prueba «largo» o «transpuesto».</div>';return;}
  const opts=['—'].concat(up.meta_cols);
  H.push('<p class="hint">El archivo debe incluir un ID por participante. Una fila de ensayo no equivale a un participante nuevo. Si solo hay columnas V1…V101, añade IDs y renombra los nodos como Variable_0…Variable_100.</p>');
  H.push('<p class="hint">'+up.blocks.length+' bloques de curvas: <span class="mono">'+esc(up.blocks.slice(0,6).join(', '))+(up.blocks.length>6?'…':'')+'</span></p>');
  H.push('<div class="grid2">'+selHtml('mSub','Sujeto (ID)',opts,guessSel(opts,GUESS.sub),1)+selHtml('mGrp','Grupo',opts,guessSel(opts,GUESS.grp))+selHtml('mCon','Condición',opts,guessSel(opts,GUESS.con))+selHtml('mSid','Lado',opts,guessSel(opts,GUESS.sid))+'</div>');
  H.push('<button id="btnMap" class="btn primary" style="max-width:280px">Aplicar mapeo</button>');
  mb.innerHTML=H.join('');
  $('#btnMap').onclick=async()=>{if(v('mSub')==='—'){mapErr('Selecciona la columna de sujeto.');return;}
   const roles={subject:v('mSub'),group:v('mGrp'),condition:v('mCon'),side:v('mSid')};
   Object.keys(roles).forEach(k=>{if(roles[k]==='—')roles[k]='';});
   const b=$('#btnMap');b.disabled=true;b.textContent='Construyendo base canónica…';
   try{const p=await pyCall('js_apply_wide',JSON.stringify(roles));afterLoad(p,S.fname);}catch(e){}
   finally{b.disabled=false;b.textContent='Aplicar mapeo';}};
 }else if(est==='long'){
  const opts=['—'].concat(up.columns);
  H.push('<div class="grid2">'+selHtml('mSub','Sujeto (ID)',opts,guessSel(opts,GUESS.sub),1)+selHtml('mNod','Punto 0–100',opts,guessSel(opts,GUESS.nod),1)+selHtml('mVal','Valor (ángulo)',opts,guessSel(opts,GUESS.val),1)+selHtml('mVar','Variable',opts,guessSel(opts,GUESS.vrb),1)+selHtml('mGrp','Grupo',opts,guessSel(opts,GUESS.grp))+selHtml('mCon','Condición',opts,guessSel(opts,GUESS.con))+selHtml('mSid','Lado',opts,guessSel(opts,GUESS.sid))+selHtml('mTri','Ensayo/Trial',opts,guessSel(opts,GUESS.tri))+'</div>');
  H.push('<div class="fld">Covariables numéricas (para regresión)<div id="covChecks" class="checks" style="max-height:120px">'+(up.numeric.length?up.numeric.map(c=>'<label class="chk"><input type="checkbox" value="'+esc(c)+'">'+esc(c)+'</label>').join(''):'<p class="hint">— ninguna candidata —</p>')+'</div></div>');
  H.push('<button id="btnMap" class="btn primary" style="max-width:280px">Aplicar mapeo</button>');
  mb.innerHTML=H.join('');
  $('#btnMap').onclick=async()=>{const req=['mSub','mNod','mVal','mVar'];
   if(req.some(id=>v(id)==='—')){mapErr('Sujeto, punto, valor y variable son obligatorios.');return;}
   const roles={subject:v('mSub'),node:v('mNod'),value:v('mVal'),variable:v('mVar'),group:v('mGrp'),condition:v('mCon'),side:v('mSid'),trial:v('mTri'),covariates:checks('covChecks')};
   Object.keys(roles).forEach(k=>{if(roles[k]==='—')roles[k]='';});
   const b=$('#btnMap');b.disabled=true;b.textContent='Construyendo base canónica…';
   try{const p=await pyCall('js_apply_long',JSON.stringify(roles));afterLoad(p,S.fname);}catch(e){}
   finally{b.disabled=false;b.textContent='Aplicar mapeo';}};
 }else{
  H.push('<div class="grid2">'+selHtml('tNode','Columna del % del ciclo (0–100)',up.columns,up.node_guess)+'<label class="fld">Delimitador del nombre<input id="tDelim" type="text" value="_"></label></div>');
  H.push('<p class="hint mono" id="tSample"></p><div class="grid2" id="tToks"></div>');
  H.push('<button id="btnMap" class="btn primary" style="max-width:280px">Aplicar mapeo</button>');
  mb.innerHTML=H.join('');
  const rebuild=()=>{const node=v('tNode'),delim=v('tDelim')||'_';
   const sample=up.columns.filter(c=>c!==node).slice(0,3);
   const er=delim.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),re=new RegExp(er);
   const parts=sample.map(s2=>String(s2).split(re));
   const ntok=Math.min(Math.max.apply(null,[1].concat(parts.map(p2=>p2.length))),6);
   $('#tSample').textContent='Ejemplos: '+sample.join('  ·  ');
   const O=[['variable','Variable'],['subject','Sujeto'],['side','Lado'],['group','Grupo'],['condition','Condición'],['ignorar','Ignorar']];
   let h='';for(let i=0;i<ntok;i++){const defv=(i===0&&ntok>1)?'subject':'variable';
    h+='<label class="fld">Token '+(i+1)+'<select id="tTok'+i+'">'+O.map(o=>'<option value="'+o[0]+'"'+(o[0]===defv?' selected':'')+'>'+o[1]+'</option>').join('')+'</select></label>';}
   $('#tToks').innerHTML=h;$('#tToks').dataset.n=ntok;};
  $('#tNode').onchange=rebuild;$('#tDelim').oninput=rebuild;rebuild();
  $('#btnMap').onclick=async()=>{const n=+($('#tToks').dataset.n||1),roles={};
   for(let i=0;i<n;i++)roles[i]=v('tTok'+i);
   const b=$('#btnMap');b.disabled=true;b.textContent='Construyendo base canónica…';
   try{const p=await pyCall('js_apply_transposed',v('tNode'),v('tDelim')||'_',JSON.stringify(roles));afterLoad(p,S.fname);}catch(e){}
   finally{b.disabled=false;b.textContent='Aplicar mapeo';}};
 }}

/* ---------- pestañas ---------- */
$$('#tabs button').forEach(b=>{b.onclick=()=>goTab(b.dataset.t);});
function goTab(t){$$('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 $$('.tab').forEach(s2=>s2.classList.toggle('on',s2.id==='t-'+t));}
