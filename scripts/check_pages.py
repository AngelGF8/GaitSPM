"""Check deployed static pages; this is not a browser or Pyodide inference test."""
import argparse
import time
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    args=parser.parse_args()
    base=args.url.rstrip('/')+'/'
    for path, markers in [('',('GaitSPM','Clinical guide')),('app/',('py-engine','anova2onerm','ancova'))]:
        url=base+path
        for attempt in range(6):
            try:
                with urlopen(Request(url,headers={'User-Agent':'GaitSPM-deployment-check'}),timeout=20) as response:
                    assert response.status==200
                    page=response.read().decode('utf-8')
                assert all(marker in page for marker in markers), 'Expected content missing'
                print('PASS: '+url)
                break
            except Exception:
                if attempt==5:raise
                time.sleep(5)


if __name__=='__main__':main()
