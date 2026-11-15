#!/usr/bin/env python3
"""Check every <form> in HTML files carries an action attribute.

Run: python3 src/html_form_action_checker.py page.html
     python3 src/html_form_action_checker.py site/
     python3 src/html_form_action_checker.py --stdin < page.html

A form with no action submits to the current URL —
usually not what the author meant, and the failure
shows up as a page reload that swallows the data
instead of an error. This tool reads each HTML file,
finds every <form>, and reports each one missing an
action attribute — or carrying an empty one, which
submits to the current URL just the same — with the
file and the line number. It exits 1 when any form
lacks a usable action, so it can fail a CI run. A
file whose forms all carry an action exits 0.

A file given directly on the command line is always
checked, whatever its name. A folder is walked for
files ending in .html or .htm only, recursively by
default (--no-recursive stops at the top level).
.git folders are never walked, and directory links
are never followed.

Forms inside HTML comments are not forms — the
parser skips them. Markup inside <script> and
<style> blocks is not parsed as HTML either, so a
"<form>" written in a JavaScript string is left
alone. Tag and attribute names are matched without
regard to case, as HTML requires.

It never rewrites a file, never touches the network,
and reads only the files and folders you point it at.
"""

import argparse
import fnmatch
import json
import os
import sys
from html.parser import HTMLParser
from pathlib import Path

__version__ = "1.0.0"

HTML_SUFFIXES = (".html", ".htm")


class FormActionParser(HTMLParser):
    """Collect every <form> without a usable action attribute.

    HTMLParser already treats <script> and <style>
    content as character data, so markup written
    inside those blocks never reaches handle_starttag.
    Comments never reach it either.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.findings = []

    def handle_starttag(self, tag, attrs):
        if tag != "form":
            return
        line, _offset = self.getpos()
        values = dict(attrs)
        if "action" not in values:
            self.findings.append({
                "line": line,
                "reason": "has no action attribute",
            })
        elif values["action"] is None or values["action"] == "":
            self.findings.append({
                "line": line,
                "reason": "has an empty action attribute",
            })


def check_text(text):
    """Check one document's text.

    Returns a list of findings, each {"line": int,
    "reason": str}, in document order.
    """
    parser = FormActionParser()
    parser.feed(text)
    parser.close()
    return parser.findings


def check_file(path):
    """Check one file. Returns (findings, error)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [], "not valid UTF-8"
    except OSError as exc:
        return [], str(exc)
    try:
        return check_text(text), None
    except Exception as exc:  # malformed markup the parser rejects
        return [], "could not be parsed: %s" % exc


def _is_html_file(path):
    return Path(path).name.lower().endswith(HTML_SUFFIXES)


def collect_files(paths, recursive=True, exclude=None):
    """Expand CLI paths into a sorted list of HTML files.

    A file given directly is always checked, whatever its
    name. A folder is walked for files ending in .html
    or .htm only. .git folders are never walked, and
    directory links are never followed.
    """
    exclude = exclude or []
    found = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            found.append(str(path))
        elif path.is_dir():
            for dirpath, dirs, files in os.walk(path, followlinks=False):
                dirs[:] = [
                    d for d in dirs
                    if d != ".git"
                    and not any(fnmatch.fnmatch(d, pat) for pat in exclude)
                ]
                for name in files:
                    candidate = Path(dirpath) / name
                    if not _is_html_file(candidate):
                        continue
                    if any(
                        fnmatch.fnmatch(str(candidate), pat)
                        or fnmatch.fnmatch(name, pat)
                        for pat in exclude
                    ):
                        continue
                    found.append(str(candidate))
                if not recursive:
                    break
        else:
            raise FileNotFoundError("no such file or folder: %s" % raw)
    seen = set()
    unique = []
    for item in found:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return sorted(unique)


def format_finding(path, finding):
    """One human-readable line for one form without an action."""
    return ("FAIL %s: <form> line %d %s"
            % (path, finding["line"], finding["reason"]))


def run(paths, recursive=True, exclude=None, as_json=False):
    """Check paths, print the report, return the exit code."""
    try:
        files = collect_files(paths, recursive=recursive, exclude=exclude)
    except FileNotFoundError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if not files:
        print("error: no HTML files found", file=sys.stderr)
        return 2
    results = []
    findings = 0
    files_with_findings = 0
    for path in files:
        bad, error = check_file(path)
        count = len(bad) + (1 if error else 0)
        if count:
            findings += count
            files_with_findings += 1
        results.append({"path": path, "findings": bad, "error": error})
    if as_json:
        print(json.dumps(
            {"files": results, "checked": len(files),
             "findings": findings},
            indent=2))
    else:
        for result in results:
            if result["error"]:
                print("FAIL %s: %s" % (result["path"], result["error"]))
            for finding in result["findings"]:
                print(format_finding(result["path"], finding))
        if findings:
            print("Checked %d file(s), %d form(s) without an action "
                  "in %d file(s)." % (len(files), findings,
                                      files_with_findings))
        else:
            print("OK — %d file(s) checked, every form carries an "
                  "action." % len(files))
    return 1 if findings else 0


def run_stdin(as_json=False):
    """Check one HTML document read from standard input."""
    text = sys.stdin.read()
    bad = check_text(text)
    findings = len(bad)
    if as_json:
        print(json.dumps(
            {"files": [{"path": "<stdin>", "findings": bad,
                        "error": None}],
             "checked": 1, "findings": findings},
            indent=2))
    else:
        for finding in bad:
            print(format_finding("<stdin>", finding))
        if findings:
            print("Checked 1 file(s), %d form(s) without an action "
                  "in 1 file(s)." % findings)
        else:
            print("OK — 1 file(s) checked, every form carries an "
                  "action.")
    return 1 if findings else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="html_form_action_checker",
        description="Check every <form> in HTML files carries "
                    "an action attribute, fail CI when one does "
                    "not.")
    parser.add_argument("paths", nargs="*",
                        help="HTML files or folders to walk")
    parser.add_argument("--no-recursive", action="store_true",
                        help="do not walk into subfolders")
    parser.add_argument("--exclude", action="append", default=[],
                        help="skip files or folders matching this pattern "
                             "(repeatable)")
    parser.add_argument("--json", action="store_true",
                        help="print the result as JSON")
    parser.add_argument("--stdin", action="store_true",
                        help="check one HTML document from standard input")
    parser.add_argument("--version", action="version",
                        version="%(prog)s " + __version__)
    args = parser.parse_args(argv)
    if args.stdin:
        if args.paths:
            parser.error("--stdin takes no file or folder arguments")
        return run_stdin(as_json=args.json)
    if not args.paths:
        parser.error("give at least one HTML file or folder")
    return run(args.paths, recursive=not args.no_recursive,
               exclude=args.exclude, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
