import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from run import simulate, PAYLOAD_SIZE
from launcher.channel import Channel

# Run a 10k-message scenario using periodic transmissions
res = simulate(10, 1, "periodic", 1, 1000)
per = 100.0 - res[2]
ch = Channel()
toa = ch.airtime(7, PAYLOAD_SIZE)

results = {"PER": per, "ToA": toa}
Path("scenario_results.json").write_text(json.dumps(results, indent=2))

# Compare with FLoRa reference
ref = json.loads(Path("flora_reference.json").read_text())
diff = abs(results["PER"] - ref["PER"])
rel = diff / ref["PER"] if ref["PER"] else diff
if rel > 0.05:
    raise SystemExit(f"PER diverges by {rel:.2%} from reference")
