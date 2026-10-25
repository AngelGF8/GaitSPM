/* Capture actual application states in English. Requires Playwright and a running native server. */
const {chromium}=require('playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 page.setDefaultTimeout(60000);
 await page.goto(process.argv[2]||'http://127.0.0.1:4173');
 await page.locator('#app').waitFor({state:'visible'});
 await page.locator('[data-lang=en]').click();
 await page.waitForFunction(()=>document.documentElement.lang==='en'&&document.querySelectorAll('[data-load]').length===8);
 fs.mkdirSync('capturas',{recursive:true});
 async function shot(name){
  await page.waitForFunction(()=>!document.querySelector('#labPanels')?.classList.contains('busy'));
  await page.evaluate(()=>document.fonts.ready);
  await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete));
  await page.screenshot({path:'capturas/'+name,animations:'disabled'});
 }
 async function load(key){
  await page.locator('.rail [data-t=datos]').click();
  await page.locator('[data-load="'+key+'"]').click();
  await page.waitForFunction(k=>S.p?.n_subj===60&&ACTIVE_DATASET?.key===k,key);
 }
 async function run(){
  await page.locator('#btnRun').click();
  await page.waitForFunction(()=>!RUNNING&&S.d&&EXPLANATION,null,{timeout:120000});
  if(await page.evaluate(()=>S.d.errors.length))throw Error('Analysis failed');
  await page.evaluate(()=>{const d=document.querySelector('#settingsDialog');if(d.open)d.close();});
 }
 await load('03_hip_oa');
 await page.evaluate(()=>window.scrollTo(0,0));
 await shot('02_ejemplo_cargado.png');
 await page.locator('#canonBox').scrollIntoViewIfNeeded();
 await shot('03_control_calidad_mapeo.png');
 await page.locator('#guideNext').click();
 await page.waitForFunction(()=>!document.querySelector('#settingsDialog').innerText.includes('Grupos'));
 await shot('04_configuracion_analisis.png');
 await run();
 await page.locator('.rail [data-t=informe]').click();
 await page.locator('#labPanels').evaluate(e=>e.scrollIntoView({block:'start'}));
 await shot('06_resultados_figura_spm.png');
 await page.locator('.rail [data-t=detalle]').click();
 await page.locator('#detBox').scrollIntoViewIfNeeded();
 await shot('07_detalle_variable.png');
 await page.locator('.rail [data-t=textos]').click();
 await page.locator('#mtEn').scrollIntoViewIfNeeded();
 await shot('08_textos_metodos_resultados.png');
 await load('07_ms_fatigue');
 await page.locator('#guideNext').click();await run();
 await page.locator('.rail [data-t=informe]').click();
 await page.locator('#labPanels').evaluate(e=>e.scrollIntoView({block:'start'}));
 await shot('12_anova_medidas_repetidas.png');
 await page.evaluate(async()=>{
  const p=await pyCall('js_load_demo',12);
  afterLoad(p,'Synthetic demonstration: pelvis, hip and knee');
  $('#unitsConfirmed').checked=true;
  $('#design').value='ttest2';renderDyn();
  $('#condSel').value='PRE';
  $$('#varsBox input').forEach(e=>e.checked=['PelvisTilt','HipFlexion','KneeFlexion'].includes(e.value));
  $('#lang').value='en';renderGuide();openSettings();
 });
 await run();
 await page.locator('.rail [data-t=informe]').click();
 await page.locator('#labPanels').evaluate(e=>e.scrollIntoView({block:'start'}));
 await shot('13_pelvis_hip_knee_english.png');
 console.log('Captured eight real English UI states with synthetic teaching examples.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
