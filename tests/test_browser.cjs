/* Run against a local server: node tests/test_browser.cjs [url]. Requires Playwright. */
const {chromium}=require('playwright');
const fs=require('fs');const path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1080}});
 const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().startsWith('http')&&!r.url().includes('127.0.0.1'))external.push(r.url());});
 await page.goto(process.argv[2]||'http://127.0.0.1:4173');
 await page.locator('#app').waitFor({state:'visible',timeout:60000});
 await page.waitForFunction(()=>document.querySelectorAll('[data-load]').length===9);
 await page.screenshot({path:'/tmp/gait_home.png',fullPage:true});
 const keys=await page.locator('[data-load]').evaluateAll(es=>es.map(e=>e.dataset.load));
 for(const key of keys){
  await page.locator('.rail [data-t=datos]').click();
  await page.locator('[data-load="'+key+'"]').click();
  await page.waitForFunction(k=>S.p?.n_subj===60 && ACTIVE_DATASET?.key===k,key);
  await page.locator('#guideNext').click();
  await page.locator('#btnRun').click();
  await page.waitForFunction(()=>!RUNNING && S.d && EXPLANATION,{},{timeout:60000});
  const summary=await page.evaluate(()=>({key:ACTIVE_DATASET.key,errors:S.d.errors,n:S.p.n_subj,nsig:S.d.nsig,design:S.cfg.design,counts:EXPLANATION.summaries.map(r=>r.samples?.map(x=>x.n))}));
  if(summary.errors.length)throw Error(JSON.stringify(summary));
  if(summary.n!==60)throw Error('Wrong N');
  console.log(JSON.stringify(summary));
  if(['03_hip_oa','07_ms_fatigue','08_acl_retest'].includes(key))await page.screenshot({path:'/tmp/gait_'+key+'.png',fullPage:true});
 }
 await page.evaluate(async()=>await setLanguage('en'));
 await page.waitForFunction(()=>document.documentElement.lang==='en'&&!RUNNING);
 await page.locator('#modeLab').click();await page.locator('#modeGuided').click();
 await page.evaluate(async()=>await setLanguage('es'));
 await page.waitForFunction(()=>document.documentElement.lang==='es');
 for(const key of keys){
  const file=path.resolve(__dirname,'../datasets/synthetic',key,key+'.xlsx');
  await page.locator('.rail [data-t=datos]').click();
  await page.locator('#file').setInputFiles(file);
  await page.locator('#upBox').waitFor({state:'visible'});
  await page.locator('#btnMap').click();
  await page.waitForFunction(k=>S.p?.example?.key===k,key,{timeout:60000});
  console.log('XLSX import',key,'recognised');
 }
 const f=path.resolve(__dirname,'../datasets/synthetic/03_hip_oa/curves_wide_es.csv');
 await page.locator('#file').setInputFiles(f);await page.locator('#upBox').waitFor({state:'visible'});await page.locator('#btnMap').click();
 await page.waitForFunction(()=>S.p?.example?.key==='03_hip_oa',{},{timeout:60000});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/gait_mobile.png',fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);
 if(errors.length||external.length||overflow)throw Error(JSON.stringify({errors,external,overflow}));
 console.log('PASS: 9 examples, 9 XLSX imports, Spanish CSV, modes, languages, mobile overflow, no external requests');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
