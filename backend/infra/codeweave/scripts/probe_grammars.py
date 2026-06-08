#!/usr/bin/env python3
"""Probe Tree-sitter grammars for languages detected in a repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_CODEWEAVE = Path(__file__).resolve().parents[1]
if str(_CODEWEAVE) not in sys.path:
    sys.path.insert(0, str(_CODEWEAVE))

from infrastructure.parser.grammar_probe import probe_languages, probe_repository
from infrastructure.parser.language_specs import LANGUAGE_REGISTRY, supports_semantic_chunking


def _all_semantic_languages() -> list[str]:
    return sorted(
        lang
        for lang, spec in LANGUAGE_REGISTRY.items()
        if supports_semantic_chunking(spec)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='Probe Tree-sitter grammars for CodeWeave.')
    parser.add_argument(
        'root',
        nargs='?',
        type=Path,
        default=Path.cwd(),
        help='Repository root to scan (default: cwd)',
    )
    parser.add_argument(
        '--all-semantic',
        action='store_true',
        help='Probe every language with AST semantic chunking (ignore scan)',
    )
    parser.add_argument('--json', action='store_true', help='Emit JSON report')
    args = parser.parse_args()

    if args.all_semantic:
        results = probe_languages(_all_semantic_languages())
        payload = {
            'mode': 'all_semantic',
            'grammars_probed': len(results),
            'grammars_ok': sum(1 for r in results if r.ok),
            'grammars_failed': [
                {'language': r.language, 'error': r.error}
                for r in results
                if not r.ok
            ],
        }
    else:
        payload = probe_repository(args.root.resolve())
        payload['mode'] = 'repository'

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"root: {payload.get('root', args.root)}")
        if payload.get('extension_counts'):
            print('top extensions:')
            for ext, count in payload['extension_counts'].items():
                print(f'  {ext}: {count}')
        print(
            f"grammars: {payload['grammars_ok']}/{payload['grammars_probed']} OK"
        )
        for item in payload.get('grammars_failed') or []:
            print(f"  FAIL {item['language']}: {item['error']}")
        if payload.get('semantic_languages'):
            print('semantic (full tier) in repo:', ', '.join(payload['semantic_languages']))

    failed = payload.get('grammars_failed') or []
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
