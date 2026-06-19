from __future__ import annotations
import json
from pathlib import Path

def relative_difference(a: float,b: float)->float:
    if b==0: raise ValueError('reference must be non-zero')
    return abs(a-b)/abs(b)

def validate_benchmark(payload: dict, duty_tolerance: float=0.05, mass_tolerance: float=1e-9)->dict:
    if duty_tolerance<=0 or mass_tolerance<0: raise ValueError('invalid tolerance')
    scenarios=payload.get('scenarios') or []
    if not scenarios: raise ValueError('no scenarios')
    rows=[]
    for s in scenarios:
        required={'hydrogen_kg_day','dwsim_duty_kW','independent_duty_kW','mass_balance_error_kg_s','solve_ok','warning_count'}
        if not required.issubset(s): raise ValueError('missing scenario fields')
        diff=relative_difference(float(s['dwsim_duty_kW']),float(s['independent_duty_kW']))
        ok=bool(s['solve_ok']) and int(s['warning_count'])==0 and abs(float(s['mass_balance_error_kg_s']))<=mass_tolerance and diff<=duty_tolerance and float(s['dwsim_duty_kW'])>0
        rows.append({**s,'duty_relative_difference':diff,'pass':ok})
    neg=payload.get('negative_case',{})
    negative_rejected=bool(neg.get('solve_ok')) and (float(neg.get('out_pressure_bar',0))<=float(neg.get('feed_pressure_bar',0)) or float(neg.get('duty_kW',0))<=0)
    monotonic=all(rows[i]['dwsim_duty_kW']<rows[i+1]['dwsim_duty_kW'] for i in range(len(rows)-1))
    return {'scenario_count':len(rows),'all_scenarios_pass':all(r['pass'] for r in rows),'max_duty_relative_difference':max(r['duty_relative_difference'] for r in rows),'negative_case_rejected':negative_rejected,'duty_monotonic':monotonic,'validation_pass':all(r['pass'] for r in rows) and negative_rejected and monotonic,'rows':rows}

def load_and_validate(path: str|Path)->dict:
    return validate_benchmark(json.loads(Path(path).read_text(encoding='utf-8')))
