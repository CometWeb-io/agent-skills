"""Content-addressed closure for the local protected workflow (no installed copies)."""
from pathlib import Path
import hashlib

SKILLS = ("skill-orchestrator", "skill-orchestrator-multiagent", "brief-architect",
          "evidence-researcher", "ai-council", "web-app-auditor", "product-operator", "content-writer")
EXCLUDED = {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv", ".git"}

def closure(root: Path) -> dict:
    names = set()
    required = [*("skills/" + skill + "/SKILL.md" for skill in SKILLS),
        "skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py",
        "skills/skill-orchestrator/scripts/orchestrate_kernel.py",
        "skills/skill-orchestrator/scripts/worker_compiler.py",
        "skills/brief-architect/scripts/kernel.py",
        "skills/brief-architect/references/prd-output.schema.json",
        "skills/evidence-researcher/scripts/evidence_kernel.py",
        "skills/ai-council/scripts/council_kernel.py",
        "skills/web-app-auditor/scripts/validate_report.py",
        "skills/product-operator/scripts/operator_kernel.py",
        "skills/content-writer/scripts/kernel.py"]
    for name in required:
        if not (root / name).is_file():
            raise ValueError("complete local pilot source required: " + name)
    for folder in [*("skills/" + skill for skill in SKILLS), "registry", "protocol", "specialist-profiles"]:
        base = root / folder
        if not base.is_dir():
            raise ValueError("missing runtime source directory: " + folder)
        for p in base.rglob("*"):
            if p.is_file() and not EXCLUDED.intersection(p.relative_to(root).parts) and p.suffix != ".pyc":
                if not p.resolve().is_relative_to(root.resolve()):
                    raise ValueError("runtime source escapes pinned root")
                names.add(str(p.relative_to(root)))
    return {name: "sha256:" + hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(names)}
