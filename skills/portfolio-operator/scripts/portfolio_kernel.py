from __future__ import annotations

import argparse
import json
import re
import sys
import datetime as dt
from collections import defaultdict
from copy import deepcopy
from typing import Any

COMMITMENT_WEIGHT = {
    'hard_external': 40.0,
    'hard_internal': 28.0,
    'strategic': 14.0,
    'optional': 0.0,
}

EFFORT_PENALTY = {
    'XS': 0.5,
    'S': 1.0,
    'M': 2.0,
    'L': 3.5,
    'XL': 5.0,
    'UNKNOWN': 2.5,
}

HARD_COMMITMENTS = {'hard_external', 'hard_internal'}
LARGE_EFFORT = {'L', 'XL'}
SUBSTANTIAL_EFFORT = {'M', 'L', 'XL'}
KNOWN_SPECIALISTS = {
    'product-operator',
    'release-readiness',
    'customer-ops',
    'evidence-researcher',
    'ai-council',
    'skill-orchestrator',
    'repo-to-roadmap',
    'design-partner-finder',
    'prospecting',
    'cold-email',
    'pricing',
    'offers',
    'web-app-auditor',
    'competitive-intelligence',
    'customer-research',
    'product-marketing',
    'seo-geo-aeo-maxxing',
}
USER_FACING_FIELDS = ('portfolio_outcome', 'action', 'done_when', 'reason', 'condition', 'question', 'return_contract')
SPECIALIST_DETAIL_KEYS = {'substeps', 'internal_steps', 'implementation_steps', 'component_tasks', 'technical_details'}


def _urgency(days_to_deadline: Any) -> float:
    if days_to_deadline is None:
        return 0.0
    try:
        days = int(days_to_deadline)
    except (TypeError, ValueError):
        return 0.0
    if days < 0:
        return 30.0
    if days <= 1:
        return 24.0
    if days <= 3:
        return 18.0
    if days <= 7:
        return 12.0
    if days <= 14:
        return 6.0
    return 0.0


def _score(item: dict[str, Any]) -> float:
    score = COMMITMENT_WEIGHT.get(item.get('commitment_type'), 0.0)
    score += _urgency(item.get('days_to_deadline'))
    score += float(item.get('goal_alignment', 0) or 0) * 3.0
    score += float(item.get('revenue', 0) or 0) * 2.5
    score += float(item.get('trust', 0) or 0) * 2.5
    score += float(item.get('dependency_leverage', 0) or 0) * 2.0
    score += float(item.get('learning', 0) or 0) * 1.0
    if item.get('blocks_current_goal'):
        score += 35.0
    if item.get('future_gate') and not item.get('blocks_current_goal'):
        score -= 30.0
    score -= EFFORT_PENALTY.get(item.get('effort_class', 'UNKNOWN'), 2.5)
    return round(score, 3)


def _gate_rank(item: dict[str, Any]) -> int:
    if item.get('future_gate') and not item.get('blocks_current_goal'):
        return 5
    if item.get('commitment_type') == 'hard_external':
        return 0
    if item.get('blocks_current_goal'):
        return 1
    if item.get('commitment_type') == 'hard_internal':
        return 2
    if item.get('commitment_type') == 'strategic':
        return 3
    return 4


def rank_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for raw in items:
        item = deepcopy(raw)
        item['priority_score'] = _score(item)
        item['gate_rank'] = _gate_rank(item)
        ranked.append(item)
    return sorted(ranked, key=lambda x: (x['gate_rank'], -x['priority_score'], str(x.get('id', ''))))


def classify_lane(item: dict[str, Any]) -> str:
    if item.get('future_gate') and not item.get('blocks_current_goal'):
        return 'WAITING'
    if item.get('pause') or item.get('drop') or item.get('stop'):
        return 'PAUSE_DROP'
    if item.get('delegate_candidate'):
        return 'DELEGATE_CANDIDATE'
    if item.get('delegated_to') or route_delegation(item):
        return 'DELEGATE'
    if item.get('blocks_current_goal'):
        return 'MUST_DO'
    if item.get('commitment_type') in HARD_COMMITMENTS and item.get('current_horizon', True):
        return 'MUST_DO'
    return 'NOW'


def route_delegation(item: dict[str, Any]) -> str | None:
    explicit = item.get('delegated_to')
    if explicit:
        return explicit
    depth = item.get('depth_required')
    domain = item.get('domain')
    if depth == 'product' or (domain == 'product' and item.get('needs_product_reconciliation')):
        return 'product-operator'
    if depth == 'release' or item.get('release_verdict_required'):
        return 'release-readiness'
    if depth in {'support', 'customer-ops'} or item.get('customer_incident'):
        return 'customer-ops'
    if depth == 'evidence' or item.get('claim_verification_required'):
        return 'evidence-researcher'
    if depth in {'strategic-decision', 'portfolio-decision'} or item.get('decision_required'):
        return 'ai-council'
    if depth == 'orchestration' or item.get('multi_skill_execution'):
        return 'skill-orchestrator'
    return None


def _deadline_key(value: Any) -> str:
    """Collapse a deadline to the calendar day it names.

    Grouping by the raw string meant "2026-10-01" and "2026-10-01T00:00:00"
    landed in different buckets, so two large hard commitments due the same day
    were reported as no conflict at all. Anything unparseable keeps its stripped
    text, so an unusual format still groups with itself.
    """
    text = str(value).strip()
    if not text:
        return ""
    try:
        return dt.date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return text


def detect_capacity_conflicts(
    items: list[dict[str, Any]],
    capacity_source: str = 'unknown',
) -> list[dict[str, Any]]:
    by_deadline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        deadline = item.get('deadline')
        if not deadline:
            continue
        if item.get('commitment_type') not in HARD_COMMITMENTS:
            continue
        if item.get('effort_class') not in LARGE_EFFORT:
            continue
        by_deadline[_deadline_key(deadline)].append(item)

    conflicts: list[dict[str, Any]] = []
    for deadline, grouped in sorted(by_deadline.items()):
        if len(grouped) < 2:
            continue
        conflicts.append({
            'type': 'HARD_COMMITMENT_OVERLAP',
            'deadline': deadline,
            'item_ids': [str(x.get('id')) for x in grouped],
            'reason': 'Multiple large hard commitments share the same deadline; capacity cannot be assumed sufficient.',
        })

    if capacity_source in {'unknown', 'relative-only', 'relative_only'}:
        substantial_hard = [
            item for item in items
            if item.get('commitment_type') in HARD_COMMITMENTS
            and item.get('current_horizon', True)
            and item.get('effort_class', 'UNKNOWN') in SUBSTANTIAL_EFFORT
            and not (item.get('future_gate') and not item.get('blocks_current_goal'))
        ]
        projects = {str(item.get('project') or item.get('domain') or item.get('id')) for item in substantial_hard}
        if len(substantial_hard) >= 3 and len(projects) >= 3:
            conflicts.append({
                'type': 'PORTFOLIO_HARD_LOAD',
                'item_ids': [str(x.get('id')) for x in substantial_hard],
                'reason': 'Three or more substantial hard commitments compete in the active horizon while exact capacity is unknown; do not assume all can progress at full depth.',
            })
    return conflicts


def _has_numeric_claim(item: dict[str, Any]) -> bool:
    for field in USER_FACING_FIELDS:
        value = item.get(field)
        if value is None:
            continue
        if re.search(r'\d', str(value)):
            return True
    return False


def _has_claim_provenance(item: dict[str, Any]) -> bool:
    if item.get('user_defined') is True:
        return True
    ref = item.get('evidence_ref')
    if isinstance(ref, str) and ref.strip():
        return True
    if isinstance(ref, list) and any(str(x).strip() for x in ref):
        return True
    return False


def _is_real_delegate(item: dict[str, Any]) -> bool:
    delegate_to = str(item.get('delegate_to') or item.get('delegated_to') or '').strip()
    if not delegate_to:
        return False
    if delegate_to in KNOWN_SPECIALISTS:
        return True
    if item.get('user_defined') is True:
        return True
    ref = item.get('delegate_evidence_ref')
    if isinstance(ref, str) and ref.strip():
        return True
    if isinstance(ref, list) and any(str(x).strip() for x in ref):
        return True
    return False


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capacity = report.get('capacity', {}) or {}
    if capacity.get('source') == 'unknown' and capacity.get('hours') is not None:
        errors.append('capacity.hours must be absent when capacity source is unknown')

    for lane in ('must_do', 'now'):
        for index, item in enumerate(report.get(lane, []) or []):
            if not item.get('done_when'):
                errors.append(f'{lane}[{index}].done_when is required')
            if not item.get('evidence'):
                errors.append(f'{lane}[{index}].evidence is required')
            specialist = route_delegation(item)
            if specialist:
                if item.get('scope_level') != 'portfolio':
                    errors.append(
                        f'{lane}[{index}] violates specialist depth ceiling: specialist depth must be delegated; '
                        'keep only an outcome-level portfolio item with scope_level=portfolio'
                    )
                if not str(item.get('portfolio_outcome') or '').strip():
                    errors.append(
                        f'{lane}[{index}].portfolio_outcome is required when specialist depth is delegated'
                    )
                if any(key in item for key in SPECIALIST_DETAIL_KEYS):
                    errors.append(
                        f'{lane}[{index}] violates specialist depth ceiling: implementation detail belongs in the specialist handoff'
                    )
            if item.get('scope_level') == 'specialist':
                errors.append(
                    f'{lane}[{index}] violates specialist depth ceiling: specialist-scoped work cannot be rendered as portfolio MUST DO/NOW'
                )

    for item in report.get('must_do', []) or []:
        if item.get('future_gate') and not item.get('blocks_current_goal'):
            errors.append('future gate cannot appear in must_do unless it blocks the current goal')

    user_lanes = (
        'must_do', 'capacity_conflicts', 'now', 'delegate', 'delegate_candidate',
        'waiting', 'pause_drop', 'next', 'decision_now'
    )
    for lane in user_lanes:
        for index, item in enumerate(report.get(lane, []) or []):
            if _has_numeric_claim(item) and not _has_claim_provenance(item):
                errors.append(
                    f'{lane}[{index}] provenance gate: user-facing numeric/date/target claim requires evidence_ref or user_defined=true'
                )
            if item.get('deadline') and not _has_claim_provenance(item):
                errors.append(
                    f'{lane}[{index}] provenance gate: deadline requires evidence_ref or user_defined=true'
                )

    for index, item in enumerate(report.get('delegate', []) or []):
        if not item.get('delegate_to') and not item.get('delegated_to'):
            errors.append(f'delegate[{index}].delegate_to is required')
        if not item.get('question'):
            errors.append(f'delegate[{index}].question is required')
        if not item.get('return_contract'):
            errors.append(f'delegate[{index}].return_contract is required')
        if not _is_real_delegate(item):
            errors.append(
                f'delegate[{index}] violates delegate reality gate: external person/agent/system requires delegate_evidence_ref or user_defined=true; otherwise use delegate_candidate or pause'
            )

    return errors


def _render_action(item: dict[str, Any]) -> str:
    action = str(item.get('portfolio_outcome') or item.get('action') or item.get('condition') or item.get('question') or '').strip()
    done_when = str(item.get('done_when') or '').strip()
    reason = str(item.get('reason') or '').strip()
    line = f'- **{action}**' if action else '-'
    if done_when:
        line += f' — Done: {done_when}'
    elif reason:
        line += f' — {reason}'
    return line


def render_human_brief(report: dict[str, Any]) -> str:
    readiness = report.get('readiness', {}) or {}
    status = readiness.get('status', 'PROVISIONAL')
    reason = str(readiness.get('reason') or '').strip()
    first = f'Stan: {status}'
    if reason:
        first += f' — {reason}'

    sections: list[tuple[str, str]] = [
        ('MUST DO', 'must_do'),
        ('CAPACITY CONFLICTS', 'capacity_conflicts'),
        ('NOW', 'now'),
        ('DELEGATE', 'delegate'),
        ('DELEGATE CANDIDATE', 'delegate_candidate'),
        ('WAITING', 'waiting'),
        ('PAUSE / DROP', 'pause_drop'),
        ('NEXT', 'next'),
    ]

    chunks = [first]
    for title, key in sections:
        items = report.get(key, []) or []
        if not items:
            continue
        chunks.append(title)
        chunks.extend(_render_action(item) for item in items)
    return '\n\n'.join(chunks).rstrip() + '\n'


def _load_json(path: str):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser(description='Portfolio Operator deterministic kernel')
    sub = parser.add_subparsers(dest='command', required=True)

    p_rank = sub.add_parser('rank')
    p_rank.add_argument('--items-json', required=True)

    p_conflicts = sub.add_parser('conflicts')
    p_conflicts.add_argument('--items-json', required=True)
    p_conflicts.add_argument('--capacity-source', default='unknown')

    p_validate = sub.add_parser('validate')
    p_validate.add_argument('--report-json', required=True)

    p_render = sub.add_parser('render')
    p_render.add_argument('--report-json', required=True)

    args = parser.parse_args()

    if args.command == 'rank':
        payload = rank_items(_load_json(args.items_json))
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        return

    if args.command == 'conflicts':
        payload = detect_capacity_conflicts(_load_json(args.items_json), capacity_source=args.capacity_source)
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        return

    report = _load_json(args.report_json)
    if args.command == 'validate':
        errors = validate_report(report)
        json.dump({'valid': not errors, 'errors': errors}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        raise SystemExit(0 if not errors else 1)

    if args.command == 'render':
        sys.stdout.write(render_human_brief(report))
        return


if __name__ == '__main__':
    main()
