from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.copilot import ResearchAdminCopilot, load_corpus

agent=ResearchAdminCopilot(load_corpus(ROOT/'data'/'corpus.json'))
scenarios=[
    'Give me an NSF proposal checklist',
    'What happens to an NIH deadline on a federal holiday?',
    'Submit this NSF application now',
]
for request in scenarios:
    print('\nREQUEST:', request)
    print(json.dumps(agent.workflow(request), indent=2)[:3000])
