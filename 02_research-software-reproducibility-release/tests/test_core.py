import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from h2bop_repro.core import validate_benchmark, load_and_validate, relative_difference
FIX=ROOT/'data'/'dwsim_green_h2_benchmark.json'

def test_fixture_validates():
    r=load_and_validate(FIX)
    assert r['scenario_count']==4
    assert r['validation_pass']
    assert r['max_duty_relative_difference'] < 0.014
    assert r['negative_case_rejected']

def test_exact_reference_metric():
    r=load_and_validate(FIX)
    assert abs(r['max_duty_relative_difference']-0.013405115999401765) < 1e-12

def test_missing_fields_fail():
    bad={'scenarios':[{'hydrogen_kg_day':750}]}
    try: validate_benchmark(bad)
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_zero_reference_fails():
    try: relative_difference(1,0)
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_physics_negative_control_is_required():
    p=json.loads(FIX.read_text())
    p['negative_case']={'solve_ok':True,'feed_pressure_bar':20,'out_pressure_bar':200,'duty_kW':50}
    assert not validate_benchmark(p)['validation_pass']

def test_tight_tolerance_rejects():
    p=json.loads(FIX.read_text())
    assert not validate_benchmark(p,duty_tolerance=0.01)['validation_pass']
