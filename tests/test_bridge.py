"""Browser bridge contract and native HTTP isolation/origin tests."""
import base64,json,sys,threading,unittest,urllib.request,urllib.error
from test_audit import E,ROOT,config,synthetic_dataset,synthetic_catalog
import serve


class BridgeTests(unittest.TestCase):
    def test_bridge_all_bases_languages_exports(self):
        ns=dict(E.__dict__)
        exec((ROOT/'app/simulation.py').read_text(encoding="utf-8"),ns)
        exec((ROOT/'app/bridge.py').read_text(encoding="utf-8"),ns)
        def call(name,*args):
            r=json.loads(ns[name](*args));self.assertTrue(r['ok'],r);return r
        for item in synthetic_catalog():
            p=call('js_load_synthetic',item['key']);c,m,_,vm=synthetic_dataset(item['key'])
            cfg=config(c,vars=vm.variable.tolist());call('js_run_init',json.dumps(cfg))
            for v in vm.variable:call('js_run_var',v)
            d=call('js_run_done');self.assertFalse(d['errors'])
            call('js_set_language','en');d=call('js_run_done');self.assertIn('Joint',d['table']['columns'])
            call('js_fig_panels',json.dumps(vm.variable.tolist()))
            for method in ['js_table_csv','js_table_xlsx']:
                r=call(method);self.assertGreater(len(base64.b64decode(r['b64'])),100)
            for fmt in ['png','svg','pdf']:call('js_export_detail',vm.variable.iloc[0],fmt,100)

    def test_http_origins_operations_sessions(self):
        server=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        base=f'http://127.0.0.1:{server.server_port}'
        def post(name,args=[],token='AuditSessionA',origin=None):
            headers={'Content-Type':'application/json','X-GaitSPM-Session':token}
            if origin:headers['Origin']=origin
            req=urllib.request.Request(base+'/api/call',json.dumps(dict(name=name,args=args)).encode(),headers=headers)
            with urllib.request.urlopen(req) as response:return json.load(response)
        try:
            for item in synthetic_catalog():
                for ext in ('.csv','.xlsx'):
                    name=item['key']+ext
                    with urllib.request.urlopen(base+'/examples/'+name) as response:
                        self.assertEqual(response.read(),(ROOT/'datasets/synthetic'/item['key']/name).read_bytes())
            with self.assertRaises(urllib.error.HTTPError) as missing:
                urllib.request.urlopen(base+'/examples/../serve.py')
            self.assertEqual(missing.exception.code,404)
            self.assertTrue(post('js_ping')['ok'])
            with self.assertRaises(urllib.error.HTTPError) as err:post('js_ping',origin='https://attacker.invalid')
            self.assertEqual(err.exception.code,403)
            with self.assertRaises(urllib.error.HTTPError):post('__import__')
            self.assertTrue(post('js_load_synthetic',['01_fai'])['ok'])
            self.assertNotIn('canon',serve.get_session('AuditSessionB')['STATE'])
        finally:
            server.shutdown();server.server_close();t.join()
            for token in ['AuditSessionA','AuditSessionB']:
                if token in serve.SESSIONS:serve.SESSIONS.pop(token)['tmp'].cleanup()


if __name__=='__main__':unittest.main(verbosity=2)
