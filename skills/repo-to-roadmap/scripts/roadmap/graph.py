"""Hard dependency graph analysis."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List

from .util import normalized


def graph_report(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError("graph items must be a list of objects")
    for item in items:
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            raise ValueError("graph items require nonempty string IDs")
        deps_input = item.get("depends_on", [])
        if not isinstance(deps_input, list) or any(not isinstance(d, str) or not d.strip() for d in deps_input):
            raise ValueError("dependencies must be a list of nonempty string IDs")
        if len({d.strip() for d in deps_input}) != len(deps_input):
            raise ValueError("duplicate dependency references")
    ids = [normalized(item.get("id")) for item in items if item.get("id") is not None]
    duplicate_ids = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    id_set = set(ids)
    deps: Dict[str, List[str]] = {}
    missing: Dict[str, List[str]] = {}

    for item in items:
        if item.get("id") is None:
            continue
        item_id = normalized(item["id"])
        raw_deps = item.get("depends_on", []) or []
        if not isinstance(raw_deps, list):
            raise ValueError(f"depends_on for {item_id} must be a list")
        parsed = [normalized(dep) for dep in raw_deps]
        deps[item_id] = [dep for dep in parsed if dep in id_set]
        absent = [dep for dep in parsed if dep not in id_set]
        if absent:
            missing[item_id] = sorted(set(absent))

    indegree = {item_id: 0 for item_id in id_set}
    outgoing: Dict[str, List[str]] = defaultdict(list)
    for item_id, item_deps in deps.items():
        for dep in item_deps:
            outgoing[dep].append(item_id)
            indegree[item_id] += 1

    queue = deque(sorted([item_id for item_id, degree in indegree.items() if degree == 0]))
    order: List[str] = []
    wave_index: Dict[str, int] = {item_id: 0 for item_id in queue}
    longest_chain: Dict[str, List[str]] = {item_id: [item_id] for item_id in queue}

    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(outgoing[node]):
            candidate_chain = longest_chain.get(node, [node]) + [child]
            if len(candidate_chain) > len(longest_chain.get(child, [])):
                longest_chain[child] = candidate_chain
            wave_index[child] = max(wave_index.get(child, 0), wave_index.get(node, 0) + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    cycle_nodes = sorted([item_id for item_id, degree in indegree.items() if degree > 0])
    waves: Dict[int, List[str]] = defaultdict(list)
    if not cycle_nodes:
        for node in order:
            waves[wave_index.get(node, 0)].append(node)

    transitive_unblocks: Dict[str, int] = {}
    for node in id_set:
        seen: set[str] = set()
        stack = list(outgoing[node])
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(outgoing[child])
        transitive_unblocks[node] = len(seen)

    leverage = sorted(
        ({"id": node, "direct_unblocks": len(outgoing[node]), "transitive_unblocks": transitive_unblocks[node]} for node in id_set),
        key=lambda row: (-row["transitive_unblocks"], -row["direct_unblocks"], row["id"]),
    )
    valid = not duplicate_ids and not missing and not cycle_nodes
    critical_chain = max(longest_chain.values(), key=lambda chain: (len(chain), chain)) if longest_chain and valid else []

    return {
        "duplicate_ids": duplicate_ids,
        "missing_dependencies": missing,
        "cycle_nodes": cycle_nodes,
        "topological_order": order if valid else [],
        "waves": [{"wave": index, "items": waves[index]} for index in sorted(waves)] if valid else [],
        "dependency_leverage": leverage[:10],
        "critical_chain_by_hard_dependency_count": critical_chain,
        "valid": valid,
        "note": "Critical chain is structural only; it is not a calendar critical path unless duration/capacity evidence exists.",
    }

