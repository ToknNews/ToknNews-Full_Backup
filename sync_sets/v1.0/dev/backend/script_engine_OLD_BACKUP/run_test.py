import json
import sys
from script_engine_v3 import generate_script

filename = sys.argv[1] if len(sys.argv) > 1 else "test_payload.json"

with open(filename, "r") as f:
    enriched = json.load(f)

script = generate_script(enriched)

print(json.dumps(script, indent=2))
