/* Guided workflow over the same data and engine as Laboratory. */
let GUIDED=true, RUNNING=false, EXPLANATION=null, UPLOAD_PENDING=false, VM_PENDING=false;
const tr=(es,en)=>LANG==='en'?en:es;
function invalidateResults(){
 S.d=null;S.cfg=null;S.tx=null;EXPLANATION=null;
 for(const p of ['inf','det','txt']){$('#'+p+'Box').hidden=true;$('#'+p+'Empty').hidden=false;}
 if($('#interpretation'))$('#interpretation').hidden=true;
 updateRibbon();renderGuide();
}
const baseAfterLoad=afterLoad;
afterLoad=function(p,name){
 S.cfg=null;EXPLANATION=null;UPLOAD_PENDING=false;VM_PENDING=false;ACTIVE_DATASET=p.example||null;
 baseAfterLoad(p,name);$('#upBox').hidden=true;$('#unitsConfirmed').checked=!!p.example;
 if(p.example)applyRecipe(p.example.recipe);
 renderGallery();renderGuide();
};
const baseBuildCfg=buildCfg;
buildCfg=function(){baseBuildCfg();$('#lang').value=LANG;$('#equalVar').checked=false;$('#band').value='';};
function applyRecipe(r){
 $('#design').value=r.design;renderDyn();
 if($('#gChecks'))$$('#gChecks input').forEach(e=>e.checked=(r.groups||[]).includes(e.value));
 if($('#pcA')){$('#pcA').value=r.cond_levels[0];$('#pcB').value=r.cond_levels[1];}
 if($('#rmChecks'))$$('#rmChecks input').forEach(e=>e.checked=r.cond_levels.includes(e.value));
 if($('#gFilt'))$('#gFilt').value=r.group_filter||'';
 if($('#condSel'))$('#condSel').value=r.cond||'';
 if($('#sideMode'))$('#sideMode').value=r.side_mode;
 $('#mode').value=r.mode;$('#mode').onchange();$('#equalVar').checked=r.equal_var;
 $('#alpha').value=r.alpha;$('#twoTailed').checked=r.two_tailed;$('#fieldCorrection').value=r.field_correction;
 $('#band').value='';renderStyleColors();
}
function setGuided(value){GUIDED=value;document.body.classList.toggle('guided',GUIDED);
 try{localStorage.setItem('gaitspm-mode',value?'guided':'lab');}catch(e){}
 renderGuide();
}
function renderGuide(){
 if(!$('#guidePanel'))return;
 $('#modeGuided').textContent=tr('Modo guiado','Guided mode');$('#modeLab').textContent=tr('Laboratorio','Laboratory');
 $('#modeGuided').setAttribute('aria-pressed',String(GUIDED));$('#modeLab').setAttribute('aria-pressed',String(!GUIDED));
 $('#guidePanel').hidden=!GUIDED;
 const stage=!S.p?0:(!$('#unitsConfirmed').checked?1:(!S.d?2:3));
 const steps=[tr('Cargar datos','Load data'),tr('Comprobar','Check data'),tr('Analizar','Analyse'),tr('Interpretar','Interpret')];
 $('#guideSteps').innerHTML=steps.map((t,i)=>'<button type="button" data-step="'+i+'" class="'+(i===stage?'current':i<stage?'complete':'')+'" '+(i===stage?'aria-current="step"':'')+'><span>'+(i+1)+'</span>'+t+'</button>').join('');
 $$('#guideSteps button').forEach(b=>b.onclick=()=>{const i=+b.dataset.step;if(i===0||i===1){goTab('datos');if(i===1&&S.p)$('#canonBox').scrollIntoView({behavior:'smooth',block:'start'});}else if(i===2&&S.p)openSettings();else if(i===3&&S.d)goTab('informe');});
 const d=ACTIVE_DATASET;
 const messages=[tr('Elige un ejemplo o carga tu CSV / Excel.','Choose an example or upload your CSV / Excel.'),
 tr('Comprueba IDs, unidades, cobertura y mapeo antes de analizar.','Check IDs, units, coverage and mapping before analysis.'),
 tr('Revisa el diseño, las variables y los grupos. Después ejecuta el análisis.','Review the design, variables and groups. Then run the analysis.'),
 tr('Lee los intervalos del ciclo, los tamaños de muestra y la interpretación.','Read the cycle intervals, sample sizes and interpretation.')];
 $('#guideMessage').textContent=messages[stage];
 $('#guideContext').textContent=d?tr(d.title_es,d.title_en)+' · 30 '+tr('casos + 30 controles','cases + 30 controls')+(d.n_conditions>1?' · '+d.n_conditions+' '+tr('condiciones repetidas','repeated conditions'):''):'';
 $('#guideNext').hidden=stage===0;
 $('#guideNext').textContent=stage===3?tr('Ver interpretación','Read interpretation'):stage===1?tr('Comprobar datos','Check data'):tr('Configurar y analizar','Configure and analyse');
 $('#guideNext').onclick=()=>{if(stage===1){goTab('datos');$('#unitsConfirmed').scrollIntoView({behavior:'smooth',block:'center'});$('#unitsConfirmed').focus();}else if(stage===2)openSettings();else{goTab('informe');$('#interpretation').scrollIntoView({behavior:'smooth',block:'start'});}};
 if(S.p){$('#groupCounts').textContent=Object.entries(S.p.group_counts||{}).map(([k,n])=>k+': n='+n).join(' · ');}
}
function renderGallery(){
 if(!CATALOG.length)return;
 $('#datasetGallery').innerHTML=CATALOG.map((d,i)=>'<article class="dataset-card '+(ACTIVE_DATASET?.key===d.key?'active':'')+'"><span class="dsnum">'+String(i+1).padStart(2,'0')+' / '+tr('SIMULADO','SIMULATED')+'</span><h2>'+esc(tr(d.title_es,d.title_en))+'</h2><p>30 '+tr('casos + 30 controles','cases + 30 controls')+'<br>'+d.n_vars+' '+tr('variables','variables')+' · '+d.n_conditions+' '+tr('condición/es','condition(s)')+' · 101 '+tr('nodos','nodes')+'</p><div class="dsfooter"><span>'+esc(T(d.short))+'</span></div><div class="example-actions"><button data-load="'+d.key+'">'+tr('Cargar ejemplo','Load example')+'</button><button data-csv="'+d.key+'">CSV</button>'+(nativeMode?'<a href="/examples/'+d.key+'.xlsx" download>'+tr('Excel','Excel')+'</a>':'')+'</div></article>').join('');
 $$('[data-load]').forEach(b=>b.onclick=async()=>{if(RUNNING)return;b.disabled=true;try{const d=CATALOG.find(x=>x.key===b.dataset.load);const p=await pyCall('js_load_synthetic',d.key);afterLoad(p,tr(d.title_es,d.title_en));const note=d.source_note_en?tr(d.source_note_es,d.source_note_en):d.url?tr('Parámetros escalares heredados de v1.3. Forma temporal simulada.','Scalar parameters inherited from v1.3. Simulated waveform shapes.'):tr('Escenario didáctico hipotético. No reproduce efectos clínicos publicados.','Hypothetical teaching scenario. Does not reproduce published clinical effects.');$('#datasetSource').innerHTML=esc(note)+(d.url?' <a target="_blank" rel="noopener" href="'+esc(d.url)+'">'+esc(d.citation)+'</a>':'');toast('Ejemplo cargado');}catch(e){showErr(tr('Carga','Load'),{error:e.message});}finally{b.disabled=false;}});
 $$('[data-csv]').forEach(b=>b.onclick=async()=>{const r=await pyCall('js_download_example_csv',b.dataset.csv);dl(r.b64,r.mime,r.fname);});
}
const oldCollectCfg=collectCfg;
collectCfg=function(){const r=oldCollectCfg();if(UPLOAD_PENDING)r.probs.push(tr('Aplica primero el mapeo del archivo nuevo o vuelve a cargar un ejemplo.','Apply the new file mapping first or reload an example.'));if(VM_PENDING)r.probs.push(tr('Guarda la clasificación articular antes de analizar.','Save the joint mapping before analysing.'));if(!$('#unitsConfirmed').checked)r.probs.push(tr('Confirma que los ángulos están en grados y los ciclos correctamente segmentados.','Confirm angles are in degrees and cycles are correctly segmented.'));return r;};
function readableP(p){return p<.001?'p < 0.001':'p = '+p.toFixed(3);}
async function showInterpretation(){
 if(!S.d)return;EXPLANATION=await pyCall('js_explain');const box=$('#interpretation');box.hidden=false;
 const text=EXPLANATION.summaries.map(r=>{
  if(r.error)return '<article class="explanation"><h3>'+esc(r.variable)+'</h3><p class="w err">'+esc(r.error)+'</p></article>';
  const n=r.samples.map(g=>esc(g.label)+' (n='+g.n+')').join(' · ');
  let content='<p class="sample-count">'+n+'</p>';
  if(!r.clusters.length)content+='<p>'+tr('No se detectan clústeres significativos con esta configuración. Esto no demuestra equivalencia ni ausencia de efecto.','No significant clusters with these settings. This does not demonstrate equivalence or absence of an effect.')+'</p>';
  for(const c of r.clusters){
   const correction=S.cfg.field_correction==='bonferroni'?tr('(ajustada entre variables)','(adjusted across variables)'):tr('(sin ajuste entre variables)','(no adjustment across variables)');
   content+='<p><b>'+c.start.toFixed(1)+'–'+c.end.toFixed(1)+' % '+tr('del ciclo','of cycle')+'</b> · '+readableP(c.p_adjusted)+' '+correction+'. ';
   if(c.mean_difference_deg!==null)content+=tr('Diferencia media descriptiva','Descriptive mean difference')+' '+esc(c.direction[0])+' − '+esc(c.direction[1])+': <b>'+c.mean_difference_deg.toFixed(2)+'°</b>. ';
   else content+=tr('El contraste global identifica diferencias; consulta los post hoc para localizar los pares.','The omnibus test detects differences; inspect post hoc tests to identify the pairs.');
   content+='</p>';
  }
  if(r.excluded.length)content+='<p class="w">'+r.excluded.length+' '+tr('participantes excluidos. Revisa los avisos.','participants excluded. Review warnings.')+'</p>';
  return '<article class="explanation"><h3>'+esc(r.variable)+'</h3>'+content+'</article>';
 }).join('');
 box.innerHTML='<div class="interpret-head"><h2>'+tr('Interpretación de este análisis','Interpretation of this analysis')+'</h2><button id="downloadAudit">'+tr('Guardar análisis JSON','Save analysis JSON')+'</button></div>'+(EXPLANATION.example?'<p class="synthetic-label">'+tr('Datos sintéticos: estos resultados no son hallazgos clínicos.','Synthetic data: these results are not clinical findings.')+'</p>':'')+text+'<p class="interpret-note">'+tr('Los valores p corresponden a clústeres, no a cada punto. La diferencia media dentro del clúster es descriptiva y se calcula tras seleccionarlo. Las bandas IC95 son puntuales. La significación estadística no establece relevancia clínica.','p-values concern clusters, not individual nodes. The within-cluster mean difference is descriptive and calculated after selection. 95% CI bands are pointwise. Statistical significance does not establish clinical relevance.')+'</p>';
 $('#downloadAudit').onclick=()=>{const value={...EXPLANATION,exported_at:new Date().toISOString()};delete value.ok;dl(btoa(unescape(encodeURIComponent(JSON.stringify(value,null,2)))),'application/json','gaitspm_analysis.json');};
 renderGuide();
}
const baseLaboratoryReady=laboratoryReady;
laboratoryReady=async function(){
 await baseLaboratoryReady();
 $('.rail-bottom').textContent='GAITSPM';
 $('.head-actions').insertAdjacentHTML('afterbegin','<div class="mode-switch"><button id="modeLab"></button><button id="modeGuided"></button></div>');
 $('main').insertAdjacentHTML('afterbegin','<section id="guidePanel" class="guide-panel" aria-label="Guided workflow"><nav id="guideSteps"></nav><div class="guide-content"><div><p id="guideMessage"></p><small id="guideContext"></small></div><button id="guideNext"></button></div></section>');
 $('#canonBox').insertAdjacentHTML('beforeend','<p id="groupCounts" class="quality no-translate"></p><label class="units-check"><input id="unitsConfirmed" type="checkbox"><span>Confirmo ángulos en grados, ciclos correctamente segmentados y mapeo articular revisado.</span></label>');
 I18N['Confirmo ángulos en grados, ciclos correctamente segmentados y mapeo articular revisado.']='I confirm angles in degrees, correctly segmented cycles and reviewed joint mapping.';
 $('#infBox').insertAdjacentHTML('afterbegin','<section id="interpretation" class="interpretation" hidden></section>');
 $('#modeLab').onclick=()=>setGuided(false);$('#modeGuided').onclick=()=>setGuided(true);
 $('#unitsConfirmed').onchange=renderGuide;
 try{GUIDED=localStorage.getItem('gaitspm-mode')!=='lab';}catch(e){}
 setGuided(GUIDED);renderGallery();
 const click=$('#btnRun').onclick;
 $('#btnRun').onclick=async()=>{
  if(RUNNING)return;
  if(collectCfg().probs.length){await click();return;}
  RUNNING=true;document.body.classList.add('running');
  const controls=$$('button,input,select').filter(e=>!e.disabled&&e.id!=='closeSettings');controls.forEach(e=>e.disabled=true);
  try{await click();if(S.d)await showInterpretation();}finally{controls.forEach(e=>e.disabled=false);RUNNING=false;document.body.classList.remove('running');renderGuide();}
 };
 const onfile=$('#file').onchange;
 $('#file').onchange=async e=>{if(!e.target.files[0])return;UPLOAD_PENDING=true;S.p=null;S.up=null;$('#upBox').hidden=true;$('#canonBox').hidden=true;$('#cfgBlk').hidden=true;$('#unitsConfirmed').checked=false;invalidateResults();await onfile(e);};
 $('#cfgBlk').addEventListener('change',()=>{if(S.d){invalidateResults();toast(tr('Configuración modificada. Ejecuta el análisis de nuevo.','Settings changed. Run the analysis again.'));}});
 $('#vmBody').addEventListener('change',()=>{VM_PENDING=true;invalidateResults();});
 const mapClick=$('#btnVm').onclick;$('#btnVm').onclick=async()=>{await mapClick();VM_PENDING=false;invalidateResults();};
};
const baseSetLanguage=setLanguage;
setLanguage=async function(lang){await baseSetLanguage(lang);renderGallery();renderGuide();if(S.d)await showInterpretation();};
