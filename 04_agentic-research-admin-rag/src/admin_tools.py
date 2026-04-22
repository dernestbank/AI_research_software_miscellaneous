from __future__ import annotations

import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYN=ROOT/"data"/"synthetic"


def _load_json(name: str):
    return json.loads((SYN/name).read_text(encoding="utf-8"))


def load_opportunities():
    return _load_json("opportunities.json")


def _tokens(text: str):
    return set(re.findall(r"[a-z0-9]+",text.lower()))


def find_opportunity(query: str) -> dict:
    opps=load_opportunities()
    q=query.strip().lower()
    for o in opps:
        if o["id"].lower() in q or q==o["id"].lower():
            return o
    qt=_tokens(q)
    scored=[]
    for i,o in enumerate(opps):
        text=f'{o["id"]} {o["sponsor"]} {o["title"]}'
        overlap=len(qt & _tokens(text))
        scored.append((overlap,-i,o))
    scored.sort(reverse=True,key=lambda x:(x[0],x[1]))
    if not scored or scored[0][0]==0:
        raise KeyError("opportunity not found")
    return scored[0][2]


def deadline_lookup(query: str) -> dict:
    o=find_opportunity(query)
    return {
        "tool":"deadline_lookup",
        "record_id":o["id"],
        "synthetic":True,
        "title":o["title"],
        "deadline":o["deadline"],
        "timezone":o["timezone"],
        "source":"synthetic opportunity register",
    }


def checklist(query: str) -> dict:
    o=find_opportunity(query)
    return {
        "tool":"checklist",
        "record_id":o["id"],
        "synthetic":True,
        "title":o["title"],
        "required_documents":list(o["required_documents"]),
        "count":len(o["required_documents"]),
        "source":"synthetic opportunity register",
    }


def compare_documents(version_a: str="call_v1.json", version_b: str="call_v2.json") -> dict:
    a=_load_json(version_a)
    b=_load_json(version_b)
    keys=sorted(set(a)|set(b))
    changes={}
    for k in keys:
        if k=="id":
            continue
        if a.get(k)!=b.get(k):
            if isinstance(a.get(k),list) and isinstance(b.get(k),list):
                av=a.get(k,[]); bv=b.get(k,[])
                changes[k]={
                    "before":av,
                    "after":bv,
                    "added":[x for x in bv if x not in av],
                    "removed":[x for x in av if x not in bv],
                }
            else:
                changes[k]={"before":a.get(k),"after":b.get(k)}
    return {
        "tool":"compare_documents",
        "synthetic":True,
        "version_a":a["id"],
        "version_b":b["id"],
        "changes":changes,
        "changed_fields":sorted(changes),
        "source":"synthetic versioned call records",
    }
