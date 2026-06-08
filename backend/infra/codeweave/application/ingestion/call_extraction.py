from __future__ import annotations

"""Extract function call sites from Tree-sitter parse trees.

Pipeline stage: **parse** (feeds call edges persisted by :mod:`persist`).

Walks call-expression nodes, resolves callee names, and returns byte-offset
records paired with caller functions during :class:`persist.IndexBatch` processing.
"""
from tree_sitter import Node
from infrastructure.logging.logger import get_logger
logger = get_logger(__name__)
_CALL_NODE_TYPES = frozenset({'call', 'call_expression', 'method_invocation'})
_CALLEE_LEAF_TYPES = frozenset({
    'identifier',
    'property_identifier',
    'field_identifier',
    'type_identifier',
    'qualified_identifier',
})

def _decode_name(code: bytes, node: Node) -> str:
    return code[node.start_byte:node.end_byte].decode('utf-8', errors='replace')

def _callee_name_from_call(code: bytes, call_node: Node) -> str | None:
    fn_node = call_node.child_by_field_name('function')
    if fn_node is None:
        for child in call_node.children:
            if child.type in _CALLEE_LEAF_TYPES:
                return _decode_name(code, child)
        return None
    if fn_node.type in _CALLEE_LEAF_TYPES:
        return _decode_name(code, fn_node)
    name_node = fn_node.child_by_field_name('name') or fn_node.child_by_field_name('property') or fn_node.child_by_field_name('field')
    if name_node is not None:
        return _decode_name(code, name_node)
    for child in reversed(list(fn_node.children)):
        if child.type in _CALLEE_LEAF_TYPES:
            return _decode_name(code, child)
    return None

def _walk_calls(node: Node, code: bytes, seen: set[int], out: list[dict]) -> None:
    if node.type in _CALL_NODE_TYPES:
        if node.start_byte not in seen:
            callee = _callee_name_from_call(code, node)
            if callee:
                seen.add(node.start_byte)
                out.append({'callee_name': callee, 'start': node.start_byte, 'end': node.end_byte})
    for child in node.children:
        _walk_calls(child, code, seen, out)

def extract_calls(code: bytes, root: Node) -> list[dict]:
    """Return sorted call-site dicts with ``callee_name`` and byte span."""
    calls: list[dict] = []
    _walk_calls(root, code, set(), calls)
    calls.sort(key=lambda item: item['start'])
    logger.debug('call_extraction: calls=%d', len(calls))
    return calls
