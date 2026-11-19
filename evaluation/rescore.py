"""Apply explicit scoring errata to saved outputs without repeating provider calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from evaluation.score import score


def rescore(directory):
    errata=Path(__file__).with_name('scoring_errata.json')
    rules=json.loads(errata.read_text())
    metadata=json.loads((directory/'metadata.json').read_text())
    source=(directory/'dataset.jsonl').read_bytes()
    if hashlib.sha256(source).hexdigest()!=metadata['dataset_sha256']:
        raise ValueError('Frozen input snapshot hash mismatch')
    cases={case['id']:case for case in map(json.loads,source.decode().splitlines())}
    for correction in rules['corrections']:
        case=copy.deepcopy(cases[correction['case_id']])
        case['reference']['facts'][correction['fact_index']].append(correction['add_alias'])
        cases[case['id']]=case
    changed=[]
    with (directory/'rescored_attempts.jsonl').open('w') as output:
        for record in map(json.loads,(directory/'attempts.jsonl').read_text().splitlines()):
            checks=score(cases[record['case_id']],record['http_status'],record.get('body',{}))
            checks={**record['checks'],**checks}
            passed=bool(checks) and all(checks.values())
            if record['checks']!=checks: changed.append({'case_id':record['case_id'],'repeat':record['repeat'],'original_passed':record['passed'],'corrected_passed':passed})
            record.update(original_checks=record['checks'],original_passed=record['passed'],checks=checks,passed=passed,scoring_version=rules['scoring_version'])
            output.write(json.dumps(record,ensure_ascii=False)+'\n')
    (directory/'scoring_errata.json').write_text(json.dumps({**rules,'changed_attempts':changed},indent=2)+'\n')
    print(json.dumps({'rescored':metadata['completed_attempts'],'changed_attempts':len(changed)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    rescore(parser.parse_args().directory)
