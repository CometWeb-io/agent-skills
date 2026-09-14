"""Bounded Markdown resource discovery for bundle linting, not a CommonMark renderer.

Supports inline links/images with titles, angle destinations, one nested parenthesis
level and reference definitions. Ignores fenced/inline code examples. This checker
proves existence, not Markdown rendering or complete semantic link coverage.
"""
from __future__ import annotations
import re

INLINE = re.compile(r'''!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|((?:\\.|[^\s()\\]|\([^()\n]*\))+))(?:[ \t]+(?:"[^"\n]*"|'[^'\n]*'|\([^\n)]*\)))?[ \t]*\)''')
REFERENCE = re.compile(r'^ {0,3}\[[^\]\n]+\]:[ \t]*(?:<([^>\n]+)>|(\S+))', re.M)


def without_code(text: str) -> str:
    rows, fence = [], None
    for line in text.splitlines(keepends=True):
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*$', line):
                fence = None
            rows.append('\n')
            continue
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            fence = (match[1][0], len(match[1])); rows.append('\n')
        else:
            rows.append(line)
    return re.sub(r'(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)', '', ''.join(rows))


def destinations(text: str) -> list[str]:
    if len(text) > 4 * 1024 * 1024:
        raise ValueError('Markdown document exceeds link-check budget')
    prose = without_code(text)
    return [re.sub(r'\\([\\()<> ])', r'\1', a or b)
            for a, b in [*INLINE.findall(prose), *REFERENCE.findall(prose)]]
