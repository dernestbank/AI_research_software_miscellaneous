from pathlib import Path
import json, sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from verify import run as run_verify, ece, threshold_sensitivity, load_rows
from negative_controls import run as run_negative, validate_prediction_file, PRED, MANIFEST
from robustness import run as run_robustness
from agent_vv import run as run_agent
from build_validation_matrix import run as run_matrix


def test_core_vv_reconciles_and_holds_only_on_drift():
    r=run_verify()
    assert r['sut_version']=='0.2.0'
    assert r['requirements_passed']==6 and r['requirements_total']==7
    failed=[x for x in r['requirements'] if not x['passed']]
    assert len(failed)==1
    assert failed[0]['name']=='Distribution-shift release gate'
    assert r['release_decision']=='HOLD'
    assert r['recomputed_metrics']['recall']>=0.60
    assert r['recomputed_metrics']['brier']<=0.02
    assert r['ece_10bin']<=0.03


def test_threshold_analysis_is_report_only_not_reselection():
    rows=load_rows(ROOT.parent/'03_ai-data-pipeline-mlops'/'artifacts'/'test_predictions.csv')
    out=threshold_sensitivity(rows)
    assert [x['threshold'] for x in out]==[0.30,0.35,0.40]
    assert out[0]['recall']>=out[-1]['recall']
    assert out[-1]['precision']>=out[0]['precision']


def test_negative_controls_detect_all_corruptions():
    r=run_negative()
    assert r['baseline_valid'] is True
    assert r['detected']==4 and r['total']==4
    assert r['all_negative_controls_detected'] is True
    reasons={x['reason'] for x in r['cases']}
    assert {'hash_mismatch','missing_required_column','probability_out_of_range','non_numeric_value'}<=reasons


def test_robustness_gates_pass_but_sparse_subgroups_are_visible():
    r=run_robustness()
    assert r['noise_gate_flip_rate_pass'] is True
    assert r['noise_gate_recall_drop_pass'] is True
    assert r['worst_prediction_flip_rate']<=0.05
    assert r['worst_recall_drop']<=0.10
    assert r['edge_probability_valid'] is True
    assert r['subgroup_by_type']['H']['positives']==0
    assert r['subgroup_by_type']['M']['positives']==4


def test_agent_vv_passes_bounded_frozen_benchmark():
    r=run_agent()
    assert r['requirements_passed']==5 and r['requirements_total']==5
    assert r['disposition']=='PASS'
    assert len(r['evaluation_sha256'])==64


def test_combined_matrix_preserves_ml_hold_and_agent_pass():
    run_negative(); run_robustness(); run_agent(); run_verify()
    r=run_matrix()
    assert r['ml_sut']['requirements_passed']==10
    assert r['ml_sut']['requirements_total']==11
    assert r['ml_sut']['disposition']=='HOLD'
    assert r['agent_sut']['disposition']=='PASS'
    assert r['negative_controls']['passed'] is True
    assert any(x['severity']=='release-blocking' for x in r['recommendations'])


def test_prediction_validator_accepts_frozen_artifact():
    expected=json.loads(MANIFEST.read_text())['predictions_sha256']
    v=validate_prediction_file(PRED,expected)
    assert v=={'valid':True,'reason':'ok'}
