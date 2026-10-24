"""v3.2 : contrôler les étapes de publication à blanc, sans tag ni appel de publication."""
import os, re, shutil, subprocess, sys, tempfile, textwrap, traceback
from pathlib import Path
from lib import Suite, HERE

ROOT=Path(HERE).parent

def t(s):
    workflow=(ROOT/'.github/workflows/release.yml').read_text()
    def etape(nom):
        m=re.search(r'^      - name: '+re.escape(nom)+r'\n(.*?)(?=^      - name: |\Z)',workflow,re.M|re.S)
        return textwrap.dedent(m[1].split('        run: |\n',1)[1])
    version=etape("Version du tag = version de l'appli")
    for tag,ok in [('v3.2',True),('v3.1',False)]:
        r=subprocess.run(['bash','-eu','-c',version],cwd=ROOT,env={**os.environ,'GITHUB_REF_NAME':tag},capture_output=True,text=True)
        s.check((r.returncode==0)==ok,'workflow : égalité app/tag '+tag+(' acceptée' if ok else ' refusée'),r.stdout+r.stderr)
    changelog=(ROOT/'CHANGELOG.md').read_text()
    s.check(changelog.splitlines().count('## v3.2')==1,'notes : une seule section exacte ## v3.2')
    attendu=changelog.split('\n## v3.2\n',1)[1].split('\n## ',1)[0].strip()
    awk=next(l for l in etape('Publier').splitlines() if l.startswith('awk '))
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(ROOT/'CHANGELOG.md',tmp)
        r=subprocess.run(['bash','-eu','-c',awk],cwd=tmp,env={**os.environ,'GITHUB_REF_NAME':'v3.2'},capture_output=True,text=True)
        notes=Path(tmp,'notes.md').read_text().strip() if r.returncode==0 else ''
        s.check(bool(attendu) and r.returncode==0 and notes==attendu,'workflow : extraction exacte et non vide des seules notes v3.2',r.stdout+r.stderr)

if __name__=='__main__':
    s=Suite('t_v32')
    try:t(s)
    except Exception:s.check(False,'exception',traceback.format_exc()[-1800:])
    sys.exit(0 if s.report() else 1)
