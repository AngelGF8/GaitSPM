"""Bilingual Streamlit Laboratory frontend. All statistics live in gaitspm_app."""
import io
import hashlib
import streamlit as st
import pandas as pd
from simulation import synthetic_catalog,synthetic_dataset


def main(E):
    st.set_page_config(page_title='GaitSPM · Laboratory',layout='wide',initial_sidebar_state='expanded')
    ss=st.session_state
    h1,h2=st.columns([8,1]);lang=h2.radio('EN / ES',['en','es'],horizontal=True,key='ui_language',label_visibility='collapsed')
    def t(es,en):return en if lang=='en' else es
    h1.markdown('## GaitSPM <span style="font-size:14px;color:#6e8097">/ '+t('Laboratorio','Laboratory')+'</span>',unsafe_allow_html=True)
    st.markdown('''<style>html,body,[class*="css"],.stApp,button,input,textarea,select,h1,h2,h3,p,label{font-family:Arial,Helvetica,sans-serif!important}.stApp{background:#f4f6f9}section[data-testid="stSidebar"]{background:#edf2f7}h1,h2,h3{color:#102c4f}div[data-testid="stMetric"]{background:white;border:1px solid #dbe2ea;border-radius:6px;padding:12px}button[kind="primary"]{background:#102c4f;border-color:#102c4f}.block-container{padding-top:1.5rem}div[data-testid="stTabs"] button{font-size:14px}</style>''',unsafe_allow_html=True)
    E.apply_matlab_style()
    def store(c,m,covs,vm,name):
        ss.canon,ss.meta,ss.covs,ss.varmap=c,m,covs,vm
        ss.data_src=name
        for k in ['results','bands','cfg','selected_vars','group_selection','condition_levels','detail_variable']:ss.pop(k,None)
    with st.sidebar:
        st.markdown('### '+t('Datos y análisis','Data & analysis'))
        cat=synthetic_catalog();key=st.selectbox(t('Base sintética','Synthetic dataset'),[x['key'] for x in cat],format_func=lambda k:next(x['title_'+lang] for x in cat if x['key']==k),key='scenario')
        if st.button(t('Cargar 20 participantes','Load 20 participants'),key='load_synthetic'):
            c,m,co,vm=synthetic_dataset(key);store(c,m,co,vm,next(x['title_'+lang] for x in cat if x['key']==key));st.rerun()
        if st.button(t('Demo original · 3 grupos / 3 condiciones','Original demo · 3 groups / 3 conditions'),key='load_demo'):
            store(*E.demo_dataset(12),'Original demo');st.rerun()
        st.caption(t('Cada base: 30 casos + 30 controles. Datos sintéticos.','Each base: 30 cases + 30 controls. Synthetic data.'))
        upload=st.file_uploader(t('Cargar CSV / Excel','Upload CSV / Excel'),type=['csv','txt','tsv','xlsx','xlsm'])
        if upload:
            token=hashlib.sha256(upload.getvalue()).hexdigest()
            df,info=E.read_upload(upload.getvalue(),upload.name)
            if info.get('hojas'):
                sheet=st.selectbox(t('Hoja de Excel','Excel sheet'),info['hojas']);df,info=E.read_upload(upload.getvalue(),upload.name,sheet)
            ss.upload_df=df
        if 'canon' in ss:
            c=ss.canon;groups=list(c.group.unique());conds=list(c.condition.unique());sides=list(c.side.unique())
            designs={'ttest2':t('t independiente','Independent t'),'paired_cond':t('t pareada · condiciones','Paired t · conditions'),'paired_side':t('t pareada · lados','Paired t · sides'),'anova1':t('ANOVA independiente','Independent ANOVA'),'anova1rm':'RM-ANOVA','regress':t('Regresión','Regression')}
            designs.update({k:E.DESIGNS[k] for k in E.ADVANCED_DESIGNS})
            design=st.selectbox(t('Diseño','Design'),list(designs),format_func=designs.get,key='design')
            cfg=dict(design=design,groups=None,cond=None,cond_levels=None,side_levels=None,group_filter=None,covariate=None,lang=lang)
            if design in ('ttest2','anova1','ancova','anova2','anova2onerm'):cfg['groups']=st.multiselect(t('Grupos','Groups'),groups,default=groups[:2 if design=='ttest2' else 3],key='group_selection')
            if design in ('paired_cond','anova1rm','anova2','anova2onerm'):cfg['cond_levels']=st.multiselect(t('Condiciones','Conditions'),conds,default=conds[:2 if design=='paired_cond' else 3],key='condition_levels')
            else:cfg['cond']=st.selectbox(t('Condición','Condition'),conds)
            if design=='paired_side':cfg['side_levels']=['L','R']
            if design in ('paired_cond','anova1rm','regress'):
                gf=st.selectbox(t('Filtrar grupo','Group filter'),['—']+groups);cfg['group_filter']=None if gf=='—' else gf
            if design=='regress':cfg['covariate']=st.selectbox(t('Covariable','Covariate'),ss.covs) if ss.covs else None
            if design in ('ancova','glm'):
                cfg['covariates']=st.multiselect('Covariates (centered)',ss.covs)
                if design=='glm':
                    import json
                    raw=st.text_input('t contrast [intercept, selected covariates]','[0,1]')
                    try:cfg['contrast']=json.loads(raw)
                    except ValueError:cfg['contrast']=[]
            if design in ('anova2','anova2onerm'):
                cfg['factor_effect']=st.selectbox('Effect (Bonferroni across 3)',['interaction','group','condition'])
            if design in E.ADVANCED_DESIGNS:
                st.caption('Parametric / equal variance. Balanced factorial designs; mixed ANOVA assumes sphericity. ANCOVA: second group minus first, common slopes.')
            sm=st.selectbox(t('Lados','Sides'),['mean','L','R'],format_func=lambda x:t('Promediar L/R','Average L/R') if x=='mean' else x);cfg['side_mode']=sm
            selected=st.multiselect(t('Variables','Variables'),ss.varmap.variable.tolist(),default=ss.varmap.variable.tolist(),key='selected_vars')
            with st.expander(t('Opciones estadísticas','Statistical options')):
                cfg['alpha']=st.number_input('α',min_value=.001,max_value=.2,value=.05,step=.01)
                cfg['mode']=st.selectbox(t('Inferencia','Inference'),['param','nonparam'],format_func=lambda x:'RFT' if x=='param' else 'SnPM')
                cfg['two_tailed']=st.checkbox(t('Bilateral','Two-tailed'),True) if design not in ('anova1','anova1rm') else False
                cfg['equal_var']=st.checkbox(t('Varianzas iguales','Equal variances'),True)
                cfg['iterations']=st.number_input(t('Permutaciones SnPM','SnPM permutations'),1000,50000,5000,1000)
                cfg['seed']=st.number_input(t('Semilla','Seed'),0,2147483647,2026,1)
                cfg['field_correction']=st.selectbox(t('Corrección entre variables','Across-variable correction'),['bonferroni','none'],format_func=lambda x:'Bonferroni' if x=='bonferroni' else t('Sin ajuste','Unadjusted'))
                cfg['posthoc']=st.checkbox(t('Post-hoc Bonferroni','Bonferroni post-hoc'),True) if design in ('anova1','anova1rm') else False
            bg=st.selectbox(t('Referencia ±DE','Reference ±SD'),['—']+groups);cfg['band_group']=None if bg=='—' else bg;cfg['band_k']=1
            cfg.update(E.plot_style(ss.get('cfg',{})))
            if st.button(t('Ejecutar análisis SPM','Run SPM analysis'),type='primary',key='run'):
                try:
                    if not selected:raise ValueError(t('Selecciona alguna variable.','Select at least one variable.'))
                    vm=ss.varmap[ss.varmap.variable.isin(selected)]
                    with st.spinner(t('Calculando…','Computing…')):ss.results,ss.bands=E.run_analysis(c,ss.meta,vm,cfg)
                    ss.cfg=cfg;st.success(t('Análisis completado. Abre Resultados.','Analysis complete. Open Results.'))
                except Exception as exc:st.error(str(exc))
    tabs=st.tabs([t('Datos','Data'),t('Resultados','Results'),t('Detalle','Detail'),t('Textos','Text')])
    with tabs[0]:
        st.caption(t('Ejemplos calibrados con parámetros publicados. Las formas temporales son simuladas.','Examples calibrated with published scalar parameters. Temporal shapes are simulated.'))
        for cols,entries in [(st.columns(3),cat[:3]),(st.columns(3),cat[3:])]:
            for col,d in zip(cols,entries):
                with col.container(border=True):
                    st.markdown('**'+d['title_'+lang]+'**');st.caption(d['short']+' · n=60');st.markdown(f'[{t("Referencia","Reference")}]({d["url"]})')
        if upload:
            st.subheader(t('Mapeo de columnas','Column mapping'));df=ss.upload_df;est,payload=E.detect_structure(df)
            kind=st.selectbox(t('Formato','Format'),['wide','long','transposed'],index=['wide','long','transposed'].index(est) if est in ['wide','long','transposed'] else 0)
            st.dataframe(df.head(),width='stretch')
            roles={};choices=['—']+list(df.columns)
            if kind in ('wide','long'):
                mapping=[('subject',['subject','sujeto','id']),('group',['group','grupo']),('condition',['condition','condicion']),('side',['side','lado'])]
                if kind=='long':mapping += [('variable',['variable']),('node',['node','punto']),('value',['value','valor']),('trial',['trial','ensayo'])]
                for role,guesses in mapping:
                    guess=next((x for x in choices if str(x).lower() in guesses),'—');v=st.selectbox(role,choices,index=choices.index(guess),key='map_'+role)
                    if v!='—':roles[role]=v
                if kind=='long':roles['covariates']=st.multiselect(t('Covariables','Covariates'),list(df.columns))
            else:
                node=st.selectbox(t('Columna de nodos','Node column'),list(df.columns));delimiter=st.text_input(t('Separador de encabezado','Header delimiter'),'|');st.caption('subject | group | condition | side | variable')
                roles={i:st.selectbox(f'Token {i+1}',['subject','group','condition','side','variable','ignorar'],index=i if i<5 else 5,key=f'token_{i}') for i in range(5)}
            if st.button(t('Aplicar mapeo','Apply mapping')):
                try:
                    if kind=='wide':c,m,co=E.canon_from_wide(df,E.find_curve_blocks(df.columns),roles)
                    elif kind=='long':c,m,co=E.canon_from_long(df,roles)
                    else:c,m,co=E.canon_from_transposed(df,node,delimiter,roles)
                    store(c,m,co,E.classify_variables(sorted(c.variable.unique())),upload.name);st.rerun()
                except Exception as exc:st.error(str(exc))
        if 'canon' in ss:
            q=E.canonical_quality(ss.canon);cs=st.columns(4)
            for col,title,value in zip(cs,[t('Participantes','Participants'),t('Curvas','Curves'),t('Variables','Variables'),t('Completitud','Completeness')],[ss.canon.subject.nunique(),q['curves'],ss.canon.variable.nunique(),f'{q["completeness_pct"]:.1f}%']):col.metric(title,value)
            ss.varmap=st.data_editor(ss.varmap,hide_index=True,width='stretch',disabled=['variable'],column_config={'joint':st.column_config.SelectboxColumn(t('Articulación','Joint'),options=['',*E.JOINT_ORDER]),'plane':st.column_config.SelectboxColumn(t('Plano','Plane'),options=['',*E.PLANE_ORDER])})
    if 'results' not in ss:
        for tab in tabs[1:]:
            with tab:st.info(t('Carga datos y ejecuta un análisis.','Load data and run an analysis.'))
        return
    ss.cfg['lang']=lang;res,bands,cfg=ss.results,ss.bands,ss.cfg
    successful=[v for v,r in res.items() if 'error' not in r]
    with tabs[1]:
        n=sum(bool(E.confirmed_clusters(r)) for r in res.values());st.caption(f'{n}/{len(res)} '+t('variables con clústeres confirmados','variables with confirmed clusters')+f' · {cfg["design"]} · α={cfg["alpha"]}')
        with st.expander(t('Apariencia · MATLAB','Appearance · MATLAB'),expanded=True):
            cols=st.columns(4)
            with cols[0]:
                cfg['interval_mode']=st.selectbox(t('Intervalo','Interval'),['sd','ci95'],format_func=lambda x:t('Media ± DE','Mean ± SD') if x=='sd' else '95% CI')
                cfg['interval_alpha']=st.slider(t('Opacidad de la banda','Band opacity'),0.,.7,.18,.01)
                cfg['show_interval_edges']=st.checkbox(t('Líneas límite','Boundary lines'),False)
            labels=res[successful[0]].get('plot',{}).get('groups',[]) if successful else []
            with cols[1]:
                for i,g in enumerate(labels[:len(cfg['line_colors'])]):
                    cfg['line_colors'][i]=st.color_picker(g['label']+' · '+t('curva','curve'),cfg['line_colors'][i],key=f'line_{i}')
                    cfg['band_colors'][i]=st.color_picker(g['label']+' · '+t('intervalo','interval'),cfg['band_colors'][i],key=f'band_{i}')
            with cols[2]:
                cfg['cluster_fill_color']=st.color_picker(t('Relleno del clúster','Cluster fill'),'#DB3D26')
                cfg['cluster_fill_alpha']=st.slider(t('Opacidad del clúster','Cluster opacity'),0.,1.,.55,.05)
            with cols[3]:
                cfg['show_cluster_bars']=st.checkbox(t('Barras del clúster (%)','Cluster bars (%)'),False)
                st.caption(t('Cambiar apariencia no repite la inferencia.','Appearance changes preserve statistical inference.'))
        joint=st.selectbox(t('Filtrar articulación','Joint filter'),['all']+E.JOINT_ORDER,format_func=lambda x:t('Todas','All') if x=='all' else E.LBL[lang]['joint'].get(x,x))
        visible=[v for v in successful if joint=='all' or res[v]['joint']==joint];page=st.number_input(t('Página (3 variables)','Page (3 variables)'),1,max(1,(len(visible)+2)//3),1)
        for col,v in zip(st.columns(3),visible[(page-1)*3:page*3]):
            with col.container(border=True):
                f,axes=E.plt.subplots(2,1,figsize=(4.1,4.4));E.plot_kin(axes[0],res[v],bands.get(v),lang,True,cfg);E.plot_spm(axes[1],res[v],lang,True,cfg);f.tight_layout();st.pyplot(f,width='stretch');E.plt.close(f)
        table=E.results_table(res,lang)
        with st.expander(t('Tabla de clústeres','Cluster table')):st.dataframe(table,width='stretch')
        for v,r in res.items():
            if 'error' in r:st.error(v+': '+r['error'])
            for w in r.get('warnings',[]):st.warning(v+': '+w)
        with st.expander(t('Exportar informe','Export report')):
            f,_=E.fig_report(res,bands,ss.varmap,lang,cfg,include_spm=True,title='GaitSPM')
            for col,fmt in zip(st.columns(3),['png','svg','pdf']):col.download_button(fmt.upper(),E.fig_to_bytes(f,fmt,300),'gaitspm.'+fmt,key='export_'+fmt)
            E.plt.close(f);st.download_button('CSV',table.to_csv(index=False).encode('utf-8-sig'),'gaitspm.csv')
            out=io.BytesIO()
            with pd.ExcelWriter(out,engine='openpyxl') as writer:table.to_excel(writer,index=False,sheet_name='SPM')
            st.download_button('XLSX',out.getvalue(),'gaitspm.xlsx')
    with tabs[2]:
        if successful:
            v=st.selectbox(t('Variable','Variable'),successful,key='detail_variable');f=E.fig_detail(res[v],bands.get(v),lang,cfg);st.pyplot(f,width='stretch');st.download_button('SVG',E.fig_to_bytes(f,'svg'),'detail.svg',key='detail_svg');E.plt.close(f)
    with tabs[3]:
        mt=E.methods_text(cfg,res,lang);rt=E.results_text(res,cfg,lang)
        st.text_area(t('Métodos','Methods'),mt,height=220);st.text_area(t('Resultados','Results'),rt,height=220);st.download_button('TXT',(mt+'\n\n'+rt).encode('utf-8'),'report.txt')
        import json
        audit = {'configuration':cfg, 'software':{'GaitSPM':E.VERSION,'spm1d':E.spm1d.__version__},
                 'models':{v:r.get('model') for v,r in res.items() if 'error' not in r}}
        st.download_button('Analysis JSON',json.dumps(audit,ensure_ascii=False,indent=2),'gaitspm_analysis.json')
        st.markdown('\n\n'.join(E.CITAS))
