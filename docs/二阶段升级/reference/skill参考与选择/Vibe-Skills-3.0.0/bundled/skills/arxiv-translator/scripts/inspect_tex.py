#!/usr/bin/env python3
"""
Heuristic scanner for untranslated English in LaTeX sources.

Usage:
    python inspect_tex.py scan <work_dir> <main_tex> <scope>

scope:
    - body: scan between \\begin{document} and \\end{document}; stop at \\appendix if present.
    - full: scan whole file(s)

Output:
    SUSPECT_COUNT=<n>
    SUSPECT=<file>:<line>:<snippet>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable

INPUT_RE = re.compile(r"\\(input|include|subfile)\{([^}]+)\}")
BEGIN_DOC_RE = re.compile(r"\\begin\{document\}")
END_DOC_RE = re.compile(r"\\end\{document\}")
APPENDIX_RE = re.compile(r"\\appendix\b")
BEGIN_BIB_RE = re.compile(r"\\begin\{thebibliography\}|\\bibliographystyle\{|\\bibliography\{")
BEGIN_TABULAR_RE = re.compile(r"\\begin\{tabular\}")
END_TABULAR_RE = re.compile(r"\\end\{tabular\}")

COMMENT_RE = re.compile(r"(?<!\\)%.*")
MATH_INLINE_RE = re.compile(r"\$[^$]+\$")
MATH_DISPLAY_RE = re.compile(r"\\\[.*?\\\]", re.DOTALL)
MATH_ENV_RE = re.compile(r"\\begin\{(equation|align|gather|multline|displaymath)\*?\}.*?\\end\{\1\*?\}", re.DOTALL)
CITE_REF_RE = re.compile(r"\\(cite|ref|label|eqref|cref|Cref|autoref|pageref|nameref|hyperref)\{[^}]*\}")
COMMAND_RE = re.compile(r"\\[a-zA-Z@]+(\[[^\]]*\])?(\{[^}]*\})*")
URL_RE = re.compile(r"https?://[^\s]+|\\url\{[^}]*\}|\\href\{[^}]*\}")

PROPER_NOUNS = {
    "transformer", "softmax", "relu", "gelu", "adam", "sgd", "bert", "gpt",
    "llama", "clip", "vit", "resnet", "imagenet", "cifar", "mnist", "coco",
    "arxiv", "github", "google", "openai", "anthropic", "meta", "microsoft",
    "nvidia", "pytorch", "tensorflow", "numpy", "scipy",
}

ACADEMIC_TERMS = {
    "et al", "e.g.", "i.e.", "etc.", "vs.", "w.r.t.", "s.t.", "iff",
    "lemma", "theorem", "proof", "corollary", "proposition", "definition",
    "figure", "table", "section", "appendix", "algorithm", "equation",
}

ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z]{4,}\b")
SENTENCE_RE = re.compile(r"[A-Z][a-z]+(?:\s+[a-z]+){3,}")


@dataclass
class Suspect:
    file: str
    line: int
    snippet: str


def strip_latex_noise(text: str) -> str:
    """Remove comments, math, commands, URLs, citations from text."""
    text = COMMENT_RE.sub("", text)
    text = MATH_DISPLAY_RE.sub("", text)
    text = MATH_ENV_RE.sub("", text)
    text = MATH_INLINE_RE.sub("", text)
    text = CITE_REF_RE.sub("", text)
    text = URL_RE.sub("", text)
    text = COMMAND_RE.sub("", text)
    return text


def is_likely_english_prose(line: str) -> bool:
    """Heuristic: line contains multiple English words forming prose."""
    cleaned = strip_latex_noise(line)
    
    lower = cleaned.lower()
    for term in PROPER_NOUNS | ACADEMIC_TERMS:
        lower = lower.replace(term.lower(), "")
    
    words = ENGLISH_WORD_RE.findall(lower)
    if len(words) < 3:
        return False
    
    if SENTENCE_RE.search(cleaned):
        return True
    
    return len(words) >= 5


def find_included_files(work_dir: str, main_tex: str) -> list[str]:
    """Recursively find all included .tex files."""
    visited = set()
    result = []
    
    def visit(rel_path: str):
        if rel_path in visited:
            return
        visited.add(rel_path)
        
        abs_path = os.path.join(work_dir, rel_path)
        if not os.path.isfile(abs_path):
            for ext in ("", ".tex"):
                candidate = abs_path + ext
                if os.path.isfile(candidate):
                    abs_path = candidate
                    break
        
        if not os.path.isfile(abs_path):
            return
        
        result.append(rel_path)
        
        try:
            content = open(abs_path, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            return
        
        for match in INPUT_RE.finditer(content):
            included = match.group(2).strip()
            if not included.endswith(".tex"):
                included += ".tex"
            base_dir = os.path.dirname(rel_path)
            included_rel = os.path.normpath(os.path.join(base_dir, included))
            visit(included_rel)
    
    visit(main_tex)
    return result


def scan_file(work_dir: str, rel_path: str, scope: str) -> Iterable[Suspect]:
    """Scan a single file for untranslated English."""
    abs_path = os.path.join(work_dir, rel_path)
    try:
        content = open(abs_path, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        return
    
    lines = content.split("\n")
    
    in_body = (scope == "full")
    in_bib = False
    in_tabular = 0
    
    for i, line in enumerate(lines, 1):
        if scope == "body":
            if BEGIN_DOC_RE.search(line):
                in_body = True
                continue
            if END_DOC_RE.search(line):
                break
            if APPENDIX_RE.search(line):
                break
        
        if not in_body:
            continue
        
        if BEGIN_BIB_RE.search(line):
            in_bib = True
        if in_bib:
            continue
        
        if BEGIN_TABULAR_RE.search(line):
            in_tabular += 1
        if END_TABULAR_RE.search(line):
            in_tabular = max(0, in_tabular - 1)
        if in_tabular > 0:
            continue
        
        if is_likely_english_prose(line):
            snippet = line.strip()[:80]
            yield Suspect(file=rel_path, line=i, snippet=snippet)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("work_dir")
    scan_parser.add_argument("main_tex")
    scan_parser.add_argument("scope", choices=["body", "full"])
    
    args = parser.parse_args()
    
    if args.command != "scan":
        parser.print_help()
        sys.exit(2)
    
    work_dir = args.work_dir
    main_tex = args.main_tex
    scope = args.scope
    
    if os.name == "nt":
        main_tex = main_tex.replace("\\", "/")
    
    files = find_included_files(work_dir, main_tex)
    
    suspects: list[Suspect] = []
    for f in files:
        suspects.extend(scan_file(work_dir, f, scope))
    
    print(f"SUSPECT_COUNT={len(suspects)}")
    for s in suspects:
        print(f"SUSPECT={s.file}:{s.line}:{s.snippet}")


if __name__ == "__main__":
    main()
