from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from retrieval import HybridRetriever, policy_answer
from admin_tools import deadline_lookup, checklist, compare_documents

ROOT=Path(__file__).resolve().parents[1]
AUDIT_PATH=ROOT/"artifacts"/"audit_log.jsonl"

PERMISSIONS={
    "viewer":{"policy_lookup","deadline_lookup","compare_documents"},
    "pi":{"policy_lookup","deadline_lookup","compare_documents","checklist"},
    "research_admin":{"policy_lookup","deadline_lookup","compare_documents","checklist"},
}
UNSUPPORTED_PATTERNS=[
    (r"\bsubmit\b|\bsubmission\b","external proposal submission"),
    (r"\bemail\b|\bsend (?:it|this|that|the proposal|the application)\b","external email/send action"),
    (r"\bupload\b","external file upload"),
    (r"\b(change|modify|edit|override)\b.*\bdeadline\b","deadline modification"),
    (r"\b(private|confidential)\b.*\b(grant|proposal|record|data)\b","private institutional data access"),
    (r"\b(patient|clinical|medical)\b.*\b(records?|data|files?)\b","clinical/private data access"),
    (r"\breveal\b.*\b(secret|credential|token|password)\b","secret/credential exfiltration"),
]


def route(query: str) -> str:
    q=query.lower()
    for pattern,_ in UNSUPPORTED_PATTERNS:
        if re.search(pattern,q):
            return "unsupported"
    if any(k in q for k in ["compare","difference","differences","what changed","changed between"]):
        return "compare_documents"
    if any(k in q for k in ["checklist","required documents","required materials","documents do i need","documents are required"]):
        return "checklist"
    if any(k in q for k in ["deadline","due date","when is syn-","when is the syn-"]):
        return "deadline_lookup"
    return "policy_lookup"


def refusal_reason(query: str) -> str:
    q=query.lower()
    for pattern,reason in UNSUPPORTED_PATTERNS:
        if re.search(pattern,q):
            return reason
    return "unsupported external or private-data action"


def trace_id(role: str, query: str, tool: str) -> str:
    return hashlib.sha256(f"{role}|{query.strip()}|{tool}".encode()).hexdigest()[:16]


def _audit(record: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True,exist_ok=True)
    with AUDIT_PATH.open("a",encoding="utf-8") as f:
        f.write(json.dumps(record,sort_keys=True)+"\n")


class ResearchAdminAgent:
    def __init__(self, retriever: HybridRetriever | None=None):
        self.retriever=retriever or HybridRetriever()

    def handle(self, query: str, role: str="viewer") -> dict:
        if role not in PERMISSIONS:
            raise ValueError(f"unknown role: {role}")
        tool=route(query)
        tid=trace_id(role,query,tool)

        if tool=="unsupported":
            result={
                "trace_id":tid,
                "role":role,
                "query":query,
                "selected_tool":"none",
                "permission":"DENIED",
                "status":"REFUSED",
                "answer":f"I cannot perform {refusal_reason(query)}. This prototype only supports bounded read-only policy/deadline/comparison and permitted checklist generation.",
                "executed_tool":False,
                "citations":[],
            }
            _audit(result)
            return result

        if tool not in PERMISSIONS[role]:
            result={
                "trace_id":tid,
                "role":role,
                "query":query,
                "selected_tool":tool,
                "permission":"DENIED",
                "status":"REFUSED",
                "answer":f"Role '{role}' is not permitted to use {tool}.",
                "executed_tool":False,
                "citations":[],
            }
            _audit(result)
            return result

        if tool=="policy_lookup":
            payload=policy_answer(query,self.retriever,top_k=3)
            answer=payload["answer"]
            citations=payload["citations"]
            sources=payload["retrieved_doc_ids"]
        elif tool=="deadline_lookup":
            payload=deadline_lookup(query)
            answer=f'{payload["title"]} deadline: {payload["deadline"]} ({payload["timezone"]}). This record is synthetic.'
            citations=[payload["record_id"]]
            sources=[payload["record_id"]]
        elif tool=="checklist":
            payload=checklist(query)
            answer="Required documents for the synthetic opportunity: "+"; ".join(payload["required_documents"])
            citations=[payload["record_id"]]
            sources=[payload["record_id"]]
        elif tool=="compare_documents":
            payload=compare_documents()
            items=[]
            for field,change in payload["changes"].items():
                items.append(f'{field}: {change["before"]} -> {change["after"]}')
            answer="Synthetic call changes: "+"; ".join(items)
            citations=[payload["version_a"],payload["version_b"]]
            sources=[payload["version_a"],payload["version_b"]]
        else:
            raise AssertionError(tool)

        result={
            "trace_id":tid,
            "role":role,
            "query":query,
            "selected_tool":tool,
            "permission":"ALLOWED",
            "status":"OK",
            "answer":answer,
            "executed_tool":True,
            "citations":citations,
            "sources":sources,
            "payload":payload,
        }
        _audit({
            "trace_id":tid,"role":role,"query":query,"selected_tool":tool,
            "permission":"ALLOWED","status":"OK","executed_tool":True,
            "citations":citations,"sources":sources,
        })
        return result


if __name__=="__main__":
    import sys
    a=ResearchAdminAgent()
    q=" ".join(sys.argv[1:]) or "What is the current NSF PAPPG?"
    print(json.dumps(a.handle(q,role="research_admin"),indent=2))
