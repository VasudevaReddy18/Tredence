# tools.py
from typing import Dict, Any

def detect_smells(code: str) -> Dict[str, Any]:
    # trivial, rule-based detector
    issues = 0
    if "eval(" in code:
        issues += 1
    if "TODO" in code:
        issues += 1
    if "print(" in code and "logger" not in code:
        issues += 1
    complexity = code.count("\n") // 10 + 1
    return {"issues": issues, "complexity": complexity}

def compute_quality_score(metrics: Dict[str, Any]) -> float:
    score = 100.0
    score -= metrics.get("issues", 0) * 10
    score -= metrics.get("complexity", 0) * 2
    return max(0.0, score)
