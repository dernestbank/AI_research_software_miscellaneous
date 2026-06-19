from __future__ import annotations
import argparse, json
from .core import load_and_validate

def main():
    p=argparse.ArgumentParser(description='Validate a frozen green-H2 compressor benchmark fixture')
    p.add_argument('fixture')
    p.add_argument('--json',action='store_true',dest='as_json')
    a=p.parse_args()
    result=load_and_validate(a.fixture)
    if a.as_json: print(json.dumps(result,indent=2))
    else: print(f"scenarios={result['scenario_count']} pass={result['validation_pass']} max_duty_diff={result['max_duty_relative_difference']:.6%} negative_rejected={result['negative_case_rejected']}")
    raise SystemExit(0 if result['validation_pass'] else 2)

if __name__=='__main__': main()
