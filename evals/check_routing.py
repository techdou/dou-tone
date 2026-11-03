#!/usr/bin/env python3
"""Compare metadata-only routing decisions with the fixture, not host activation.

Run from any directory: python3 /absolute/skill/evals/check_routing.py decisions.json
Expected input is a JSON array of {id, apply: bool, scope: str} objects. Scope
semantics and actual reference/tool use still need manual review or host traces.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def score(cases: list[dict], decisions: list[dict]) -> dict:
    if not isinstance(cases, list) or not isinstance(decisions, list):
        raise ValueError('cases and decisions must be JSON arrays')
    expected = {}
    for case in cases:
        if (not isinstance(case, dict) or not isinstance(case.get('id'), str)
                or type(case.get('expected_apply')) is not bool):
            raise ValueError('each case needs a string id and boolean expected_apply')
        key = case['id']
        if key in expected:
            raise ValueError(f'duplicate case id: {key}')
        expected[key] = case['expected_apply']
    if not expected:
        raise ValueError('empty fixture cannot establish a result')
    actual = {}
    for item in decisions:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or type(item.get('apply')) is not bool
                or not isinstance(item.get('scope'), str) or not item['scope'].strip()):
            raise ValueError('each decision needs a string id, boolean apply and nonempty scope')
        key = item['id']
        if key in actual:
            raise ValueError(f'duplicate decision id: {key}')
        actual[key] = item['apply']
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    if missing or extra:
        raise ValueError(f'incomplete decision set; missing={missing}, extra={extra}')
    mismatches = [dict(id=key, expected=value, actual=actual[key])
                  for key, value in expected.items() if value != actual[key]]
    return dict(method='metadata_decision_check', cases=len(expected),
                matched=len(expected) - len(mismatches), mismatches=mismatches,
                limitation='Not a host activation rate; manually review scope and workflow traces.')


def self_test() -> int:
    cases = [dict(id='a', expected_apply=True), dict(id='b', expected_apply=False)]
    valid = [dict(id='a', apply=True, scope='writing'), dict(id='b', apply=False, scope='layout')]
    assert score(cases, valid)['matched'] == 2
    wrong = [dict(id='a', apply=False, scope='writing'), valid[1]]
    assert score(cases, wrong)['matched'] == 1
    invalid = [valid[:1], valid + [valid[0]],
               [dict(id='a', apply=1, scope='writing'), valid[1]],
               [dict(id='a', apply=True, scope=''), valid[1]],
               [valid[0], dict(id='c', apply=False, scope='other')]]
    for decisions in invalid:
        try:
            score(cases, decisions)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid decisions accepted')
    print('PASS routing scorer self-test (7 checks)')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decisions', nargs='?', help='JSON decision array')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.decisions:
        parser.error('provide decisions.json or --self-test')
    try:
        cases = json.loads(Path(__file__).with_name('routing.json').read_text(encoding='utf-8'))
        decisions = json.loads(Path(args.decisions).read_text(encoding='utf-8'))
        result = score(cases, decisions)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result['mismatches']))


if __name__ == '__main__':
    raise SystemExit(main())
