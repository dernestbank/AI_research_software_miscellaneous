import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import evaluate

def cases(): return json.loads((ROOT/'data'/'benchmark_cases.json').read_text(encoding='utf-8'))

def test_case_count_and_balance():
    c=cases(); assert len(c)==24
    assert sum(x['workflow']=='research_admin' for x in c)==12
    assert sum(x['workflow']=='engineering_mcp' for x in c)==12
    assert {'normal','edge','adversarial','failure'} <= {x['class'] for x in c}

def test_guarded_all_expected():
    for c in cases():
        r=evaluate.score_case(c,evaluate.guarded_trace(c))
        assert r['tool_ok'] and r['arg_ok'] and r['citation_ok'] and r['unsafe_block_ok'] and r['completed']

def test_baseline_has_failures():
    rows=[evaluate.score_case(c,evaluate.baseline_trace(c)) for c in cases()]
    s=evaluate.summarize(rows)
    assert s['task_completion_rate'] < 0.8
    assert s['failure_counts']['wrong_tool'] >= 6
    assert s['failure_counts']['citation_failure'] >= 3

def test_unsafe_cases_guarded():
    uc=[c for c in cases() if c['unsafe']]
    assert len(uc)==6
    for c in uc:
        r=evaluate.score_case(c,evaluate.guarded_trace(c))
        assert r['unsafe_block_ok']

def test_schema_rejects_missing_argument():
    assert not evaluate.schema_valid('run_compressor',{'pin_bar':20})
    assert not evaluate.schema_valid('unknown_tool',{})

def test_bootstrap_reproducible():
    c=cases(); b=[evaluate.score_case(x,evaluate.baseline_trace(x)) for x in c]; g=[evaluate.score_case(x,evaluate.guarded_trace(x)) for x in c]
    x=evaluate.bootstrap_delta(b,g,draws=200,seed=7); y=evaluate.bootstrap_delta(b,g,draws=200,seed=7)
    assert x==y and x['mean_delta'] > 0

def test_adversarial_guarded_complete():
    for c in [x for x in cases() if x['class']=='adversarial']:
        assert evaluate.score_case(c,evaluate.guarded_trace(c))['completed']
