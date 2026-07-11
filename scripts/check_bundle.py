#!/usr/bin/env python3
from __future__ import annotations
import gzip, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BUNDLE=ROOT/'bundle'
def load(path):
    data=path.read_bytes(); data=gzip.decompress(data) if path.suffix=='.gz' else data; return json.loads(data)
def main():
    d=load(BUNDLE/'okf-explorer.json'); m=load(BUNDLE/'data/manifest.json'); errors=[]
    for required in ('okf-bundle.yamlld','okf-bundle.jsonld','data/adjacency/manifest.json','checksums.json'):
        if not (BUNDLE/required).is_file(): errors.append(f'missing {required}')
    relationships=sum(len(load(BUNDLE/path)) for path in m['chunks']['relationships'])
    if relationships != m['counts']['relationships']: errors.append('relationship count mismatch')
    adjacency=load(BUNDLE/m['indexes']['relationship_adjacency'])
    if adjacency.get('algorithm')!='fnv1a32-prefix-2' or adjacency.get('relationships')!=relationships: errors.append('adjacency mismatch')
    if d.get('@id')!='https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json': errors.append('canonical descriptor identity mismatch')
    if errors:
        print('bundle validation failed: '+', '.join(errors)); return 1
    print(f'bundle validation passed: {m["counts"]["datasets"]:,} records, {relationships:,} relationships, {adjacency["routes"]:,} adjacency routes'); return 0
if __name__=='__main__': raise SystemExit(main())
