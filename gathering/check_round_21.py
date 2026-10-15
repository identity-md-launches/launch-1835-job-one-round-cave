#!/usr/bin/env python3
"""Repeat new portable integration trials and exercise the repaired PNG helper."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PIN = '38219d0c9192f3566be0bf9d650c8de7de0666b562f23f3b6be7bb2d01b3dae1'
TRANSCRIPT_PIN = 'b369c4f39db608ae240242db924f635a10dfb4e7b543a18113d3b110857c497a'
LIVE_PIN = 'dbeae9bace2b3942e46c8390583466eb7c3d6bd1f3573d97b650eb46f223189b'


def main():
    assert Path.cwd().resolve() == ROOT, 'Run from repository root'
    base = Path('shared/batch-coverage')
    scratch = Path('test/scratch/batch-coverage-round21')
    scratch.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(base,scratch,dirs_exist_ok=True)
    results = []

    def run(args, expected=0, cwd=ROOT):
        result = subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,
                                text=True,timeout=45,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        assert result.returncode == expected, (args,result.stdout,result.stderr)
        results.append({'command':args,'workingDirectory':str(Path(cwd).relative_to(ROOT)),
                        'exitCode':result.returncode,'expectedExitCode':expected,
                        'stdout':result.stdout,'stderr':result.stderr,'passed':True})

    flags = ['--contract-sha256',CONTRACT_PIN,'--transcript-sha256',TRANSCRIPT_PIN,'--require-all-exercised']
    run([str(base/'test_review.py')])
    run([str(base/'review.py'),str(base/'zto-batch.contract.json'),str(base/'zto-batch.json'),*flags])
    run(['test_review.py'],cwd=ROOT/scratch)
    run(['review.py','zto-batch.contract.json','zto-batch.json',*flags],cwd=ROOT/scratch)
    run([str(base/'review.py'),str(base/'zto-batch.contract.json'),'gathering/live-zto-batch-21.json',
         '--contract-sha256',CONTRACT_PIN,'--transcript-sha256',LIVE_PIN,'--require-all-exercised'])
    run([str(base/'review.py'),str(base/'zto-batch.contract.json'),str(base/'zto-batch.json'),
         '--contract-sha256',CONTRACT_PIN,'--transcript-sha256',LIVE_PIN],expected=2)
    contract = json.loads((base/'zto-batch.contract.json').read_bytes())
    contract['properties']['reviewNote'] = {'type':'string'}
    raw = json.dumps(contract).encode()
    (scratch/'optional.contract.json').write_bytes(raw)
    run([str(base/'review.py'),str(scratch/'optional.contract.json'),str(base/'zto-batch.json'),
         '--contract-sha256',hashlib.sha256(raw).hexdigest(),'--transcript-sha256',TRANSCRIPT_PIN,
         '--require-all-exercised'],expected=1)

    spec = importlib.util.spec_from_file_location('pair_seeds_trial',ROOT/'line-4/tools/pair-seeds/pair_seeds.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    w,h,ch,rows = helper.read_png('artifacts/gathering/wall-v21.png')
    before = [bytes(row) for row in rows]
    with patch.object(helper,'read_png',return_value=(w,h,ch,rows)), patch.object(helper,'write_png') as writer:
        with contextlib.redirect_stdout(io.StringIO()) as output:
            helper.main('memory-input','memory-output')
    count = sum(a[i:i+ch]!=b[i:i+ch] for a,b in zip(before,rows) for i in range(0,len(a),ch))
    assert writer.call_count == 1 and count > 0 and f'changed_pixels={count}' in output.getvalue()
    results.append({'trial':'repaired helper on actual finished PNG, no image saved',
                    'dimensions':[w,h],'changedPixels':count,'diagnostic':output.getvalue().strip(),'passed':True})
    encoded = json.dumps(results,indent=2)+'\n'
    assert len(encoded.encode()) <= 100000
    Path('gathering/round-checks-21.json').write_text(encoded)
    print(json.dumps({'passed':True,'trials':len(results),'helperChangedPixels':count}))


if __name__ == '__main__':
    main()
