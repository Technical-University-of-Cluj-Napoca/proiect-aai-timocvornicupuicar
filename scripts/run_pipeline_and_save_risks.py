import os
import sys
import json
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))

from src.graph.workflow import run_pipeline

load_dotenv()

PDF_PATH = "data/contract_exemplu.pdf"
RISKS_OUTPUT = Path("data/contract_exemplu_risks.json")
PLOT_OUTPUT = Path("logs/risk_distribution.png")

RISKS_OUTPUT.parent.mkdir(exist_ok=True)
PLOT_OUTPUT.parent.mkdir(exist_ok=True)

print(f"Rulez pipeline pentru: {PDF_PATH}")
result = run_pipeline(PDF_PATH)

risk_map = result.get("risk_map", {})

if not risk_map:
    print("Nu s-au generat riscuri. Verifică dacă pipeline-ul a rulat corect.")
    raise SystemExit(1)

risks_list = []

for clause_id, assessment in risk_map.items():
    item = assessment.model_dump()

    if hasattr(item.get("risk_level"), "value"):
        item["risk_level"] = item["risk_level"].value

    risks_list.append(item)

with open(RISKS_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(risks_list, f, indent=4, ensure_ascii=False)

print(f"Riscuri salvate în: {RISKS_OUTPUT}")

levels = [item.get("risk_level", "NECUNOSCUT") for item in risks_list]
counter = Counter(levels)

ordered_levels = ["RIDICAT", "MEDIU", "SCAZUT", "CONFORM", "NECUNOSCUT"]
values = [counter.get(level, 0) for level in ordered_levels]

plt.figure(figsize=(8, 5))
plt.bar(ordered_levels, values)
plt.xlabel("Nivel de risc")
plt.ylabel("Număr de clauze")
plt.title("Distribuția nivelurilor de risc")
plt.tight_layout()
plt.savefig(PLOT_OUTPUT, dpi=150)
plt.close()

print(f"Grafic salvat în: {PLOT_OUTPUT}")