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
  ['GaitSPM 1.4',d.spec.title_es],
  ['Datos', 'SINTÉTICOS. 30 casos + 30 controles, 60 participantes únicos.'],
  ['Condiciones',d.spec.n_conditions],
  ['Diseño recomendado',r.design],
  ['Grupo para medidas repetidas',r.group_filter||'Control y casos'],
  ['Paso 1','Inicia GaitSPM y elige CSV / Excel.'],
  ['Paso 2','Carga este archivo. Se selecciona automáticamente Curves_Wide.'],
  ['Paso 3','Revisa ID, grupo, condición, lado y mapeo articular. Aplica el mapeo.'],
  ['Paso 4','En modo guiado, revisa el diseño propuesto y ejecuta el análisis.'],
  ['Paso 5','Consulta curvas, clústeres, interpretación, post hoc y exportaciones.'],
  ['Unidades','Grados; nodos 0–100 = porcentaje del ciclo ya segmentado.'],
  ['Formato','Una fila por participante y condición. Los nodos son columnas Variable_0…100.'],
  ['Metrics','ROM y media del ciclo son fórmulas editables. SPM se calcula en la aplicación.'],
  ['Independencia','Las condiciones repetidas NO son nuevos pacientes. IDs conservados.'],
  ['Alcance','Las formas y covarianzas son simuladas. No representan efectos clínicos demostrados.'],
  ['Inferencia','No significativo no demuestra equivalencia ni ausencia de efecto.'],
  ['Semilla',d.spec.seed],
  ['Fuente de parámetros',d.spec.citation],
  ['URL',d.spec.url||'Escenario didáctico sin fuente de efectos clínicos.'],
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
