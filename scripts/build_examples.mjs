import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2];
const payload=JSON.parse(await fs.readFile(root+'/datasets/workbook_inputs.json','utf8'));
const previewDir=process.argv[3]||root+'/.test-output/workbooks';
await fs.mkdir(previewDir,{recursive:true});
const navy='#102C4F';
function col(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
function table(sh,matrix,name){
 const last=col(matrix[0].length),end=matrix.length,range=sh.getRange('A1:'+last+end);
 range.values=matrix;range.format.font={name:'Arial',size:10,color:'#25364B'};
 range.format.rowHeight=23;range.format.columnWidth=18;sh.showGridLines=false;
 sh.getRange('A1:'+last+'1').format={fill:navy,font:{name:'Arial',color:'#FFFFFF',bold:true},rowHeight:32,wrapText:false};
 sh.freezePanes.freezeRows(1);sh.freezePanes.freezeColumns(4);
 sh.tables.add('A1:'+last+end,true,name);
 return {last,end};
}
for(const d of payload){
 const wb=Workbook.create();
 const guide=wb.worksheets.add('Guide'),metrics=wb.worksheets.add('Metrics'),data=wb.worksheets.add('Curves_Wide'),people=wb.worksheets.add('Participants');
 const {last,end}=table(data,d.wide,'Curves');
 data.getRange('E2:'+last+end).setNumberFormat('0.000');
 data.getRange('F1:'+last+'1').format.columnWidth=24;
 const pd=table(people,d.people,'People');people.getRange('F2:F'+pd.end).setNumberFormat('0.00');
 const vars=d.spec.anchors.map(x=>x[0]);
 const header=['subject','group','condition','side',...vars.flatMap(v=>[v+' ROM (deg)',v+' Mean (deg)'])];
 table(metrics,[header,...d.wide.slice(1).map(r=>[...r.slice(0,4),...vars.flatMap(()=>[null,null])])],'Metrics');
 metrics.getRange('E1:'+col(header.length)+end).format.columnWidth=27;
 for(let j=0;j<vars.length;j++){
  const start=6+j*101,finish=start+100;
  const formulas=d.wide.slice(1).map((_,i)=>{
   const row=i+2,ref=`'Curves_Wide'!${col(start)}${row}:${col(finish)}${row}`;
   return [`=MAX(${ref})-MIN(${ref})`,`=AVERAGE(${ref})`];
  });
  metrics.getRangeByIndexes(1,4+j*2,formulas.length,2).formulas=formulas;
 }
 metrics.getRange('E2:'+col(header.length)+end).setNumberFormat('0.000');
 guide.showGridLines=false;guide.tabColor=navy;
 const r=d.spec.recipe;
 const entries=[
  ['GaitSPM 1.4',d.spec.title_en],
  ['Data', 'SYNTHETIC. 30 cases + 30 controls, 60 unique participants.'],
  ['Conditions',d.spec.n_conditions],
  ['Recommended design',r.design],
  ['Repeated-measures group',r.group_filter||'Control and cases'],
  ['Step 1','Start GaitSPM and select CSV / Excel.'],
  ['Step 2','Load this file. Curves_Wide is selected automatically.'],
  ['Step 3','Review ID, group, condition, side and joint mapping. Apply the mapping.'],
  ['Step 4','In guided mode, review the proposed design and run the analysis.'],
  ['Step 5','Inspect curves, clusters, interpretation, post hoc comparisons and exports.'],
  ['Units','Degrees; nodes 0–100 = percentage of the already segmented cycle.'],
  ['Format','One row per participant and condition. Nodes are columns Variable_0…100.'],
  ['Metrics','ROM and cycle mean are editable formulas. SPM is calculated in the application.'],
  ['Independence','Repeated conditions are NOT new participants. IDs are preserved.'],
  ['Scope','Shapes and covariances are simulated. They do not represent demonstrated clinical effects.'],
  ['Inference','Non-significance does not demonstrate equivalence or absence of an effect.'],
  ['Seed',d.spec.seed],
  ['Parameter source',d.spec.citation],
  ['URL',d.spec.url||'Teaching scenario without a source for clinical effects.'],
  ['English','Synthetic data: 30 cases + 30 controls; repeated measurements preserve the same IDs.'],
  ['Interpretation','Cluster p-values refer to simulated data. They do not reproduce published study results.']
 ];
 guide.getRange('B2:C'+(entries.length+1)).values=entries;
 guide.getRange('B2:C'+(entries.length+1)).format={font:{name:'Arial',size:11,color:'#25364B'},rowHeight:33,verticalAlignment:'center'};
 guide.getRange('B2:B'+(entries.length+1)).format.columnWidth=29;
 guide.getRange('C2:C'+(entries.length+1)).format.columnWidth=105;
 guide.getRange('C2:C'+(entries.length+1)).format.wrapText=true;
 guide.getRange('B2:C2').format.font={name:'Arial',size:15,bold:true,color:navy};
 guide.getRange('B3:C3').format.fill='#EDF2F7';
 guide.getRange('C19:C20').format.rowHeight=46;
 wb.recalculate();
 const sample=await wb.inspect({kind:'table',range:'Metrics!A1:J4',include:'values,formulas',tableMaxRows:4,tableMaxCols:10,maxChars:1000});
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:20},maxChars:1000});
 await fs.writeFile(previewDir+'/'+d.spec.key+'_checks.json',JSON.stringify({sample:sample.ndjson,errors:errors.ndjson}));
 for(const [name,range] of [['Guide','B2:C22'],['Metrics','A1:H8'],['Curves_Wide','A1:H8'],['Participants','A1:G8']]){
  const png=await wb.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(previewDir+'/'+d.spec.key+'_'+name+'.png',new Uint8Array(await png.arrayBuffer()));
 }
 const xlsx=await SpreadsheetFile.exportXlsx(wb);
 await xlsx.save(root+'/datasets/synthetic/'+d.spec.key+'/'+d.spec.key+'.xlsx');
 console.log(d.spec.key,'saved',end-1,'rows,',d.spec.n_subjects,'unique participants');
}
