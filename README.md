# html-form-action-checker-cli

Check every `<form>` in HTML files carries an `action` attribute — fail CI when one does not.

[![CI](https://github.com/haiderstudio/html-form-action-checker-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/haiderstudio/html-form-action-checker-cli/actions/workflows/ci.yml) [![Licence: MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)

## What it does

`html_form_action_checker` reads each HTML file,
finds every `<form>`, and reports each one missing
an `action` attribute — or carrying an empty one,
which submits to the current URL just the same —
with the file and the line number. It exits 1 when
any form lacks a usable action, so it can fail a CI
run. A file whose forms all carry an action exits 0.

- A form with no `action` submits to the current URL
  — usually not what the author meant, and the
  failure shows up as a page reload that swallows
  the data instead of an error. This names the exact
  line, and the fix is one attribute per form.
- An empty `action=""` is reported too, with its own
  wording — it behaves exactly like a missing one.
- A file given directly on the command line is always
  checked, whatever its name. A folder is walked for
  files ending in `.html` or `.htm` only, recursively
  by default (`--no-recursive` stops at the top
  level). `.git` folders are never walked, and
  directory links are never followed.
- `--json` prints the result as JSON, and `--stdin`
  checks one HTML document read from standard input.
- Forms inside HTML comments are not forms — the
  parser skips them. Markup inside `<script>` and
  `<style>` blocks is not parsed as HTML either, so
  a `"<form>"` written in a JavaScript string or a
  stylesheet is left alone. Tag and attribute names
  are matched without regard to case, as HTML
  requires — `<FORM>` and `ACTION=` are checked
  exactly like `<form>` and `action=`.

## Who it is for

Every site owner with a form — a contact form, a
search box, a signup form, a checkout form. One
missing attribute and the form quietly reloads the
page instead of sending the data anywhere, and the
visitor thinks the site is broken. This is the gate
that stops it at the pull request.

## What it does NOT do

- It does not check form labels or button types.
  That is repo #85, html-label-checker-cli, and repo
  #88, html-button-type-checker-cli — labels and
  buttons are different checks on the same pages.
- It does not check whether the `action` URL works,
  exists, or accepts the form. A URL that answers
  is a different job — that is repo #9,
  broken-link-checker-cli, which checks links. This
  tool only checks that the attribute is there.
- It does not check input fields, validation, or
  what the server does with the data.
- It never rewrites a file, and it never touches the
  network.

## How this differs

- A fresh search of GitHub on Nov 14, 2026 found 0
  results for `"html-form-action-checker-cli"` and 1
  result for `html form action checker` —
  ManojKumarPatnaik/Major-project-list, 262 stars, a
  list of practice projects for students, not a
  checker of any kind.
- No rival checks form actions in local files.

## Install

```sh
git clone https://github.com/haiderstudio/html-form-action-checker-cli.git
cd html-form-action-checker-cli
```

There is nothing else to install: Python 3.10 or newer,
standard library only, no dependencies.

## Usage

Check one HTML file:

```sh
python3 src/html_form_action_checker.py page.html
```

A file whose forms all carry an action passes:

```sh
$ python3 src/html_form_action_checker.py examples/clean.html
OK — 1 file(s) checked, every form carries an action.
```

A file with forms missing an action fails, with the
file and line for each one:

```sh
$ python3 src/html_form_action_checker.py examples/flagged.html
FAIL examples/flagged.html: <form> line 5 has no action attribute
FAIL examples/flagged.html: <form> line 9 has no action attribute
FAIL examples/flagged.html: <form> line 13 has an empty action attribute
Checked 1 file(s), 3 form(s) without an action in 1 file(s).
```

Check a whole folder (`.html` / `.htm` files only):

```sh
$ python3 src/html_form_action_checker.py examples/
FAIL examples/flagged.html: <form> line 5 has no action attribute
FAIL examples/flagged.html: <form> line 9 has no action attribute
FAIL examples/flagged.html: <form> line 13 has an empty action attribute
Checked 3 file(s), 3 form(s) without an action in 1 file(s).
```

Check one document from standard input:

```sh
$ printf '<form method="post"><input name="x"></form>\n' | python3 src/html_form_action_checker.py --stdin
FAIL <stdin>: <form> line 1 has no action attribute
Checked 1 file(s), 1 form(s) without an action in 1 file(s).
```

Machine-readable output:

```sh
$ python3 src/html_form_action_checker.py --json examples/flagged.html
{
  "files": [
    {
      "path": "examples/flagged.html",
      "findings": [
        {
          "line": 5,
          "reason": "has no action attribute"
        },
        {
          "line": 9,
          "reason": "has no action attribute"
        },
        {
          "line": 13,
          "reason": "has an empty action attribute"
        }
      ],
      "error": null
    }
  ],
  "checked": 1,
  "findings": 3
}
```

Exit codes: 0 when every form carries an action, 1
when any form lacks one or a file cannot be read, 2
for a usage error (a missing path, a bad flag, or no
HTML files found).

## Examples

A form in a comment and a form written inside a
script string are not forms, and `examples/clean.html`
holds both — it passes:

```sh
$ python3 src/html_form_action_checker.py examples/clean.html
OK — 1 file(s) checked, every form carries an action.
```

Uppercase tags, an action with a query string, and a
self-closing form are all handled —
`examples/edge.html` has all of them, and it passes:

```sh
$ python3 src/html_form_action_checker.py examples/edge.html
OK — 1 file(s) checked, every form carries an action.
```

A form that only has a `method` still fails — the
method is not the action:

```sh
$ printf '<form method="post"><input name="x"></form>\n' > /tmp/form.html
$ python3 src/html_form_action_checker.py /tmp/form.html
FAIL /tmp/form.html: <form> line 1 has no action attribute
Checked 1 file(s), 1 form(s) without an action in 1 file(s).
```

Run every bundled example at once with `sh
examples/run-example.sh` — the output is saved in
[examples/sample-output.md](examples/sample-output.md).

## How it is tested

```sh
python3 tests/test_html_form_action_checker.py
```

The tests cover form detection (a form with an
action passes, a form with no action fails, an empty
action fails, a bare `action` with no value fails, a
form with only a `method` fails, several forms in one
file in document order, an uppercase `<FORM>` and
`ACTION=`, a self-closing form with an action
passes, a self-closing form without one fails, an
action with a query string passes, a form on the
same line as other markup, a form split across
lines reports the line the tag starts on, a file
with no forms passes, an empty document passes),
skipping (a form in a comment, a form in a script
string, a form in a style block, unclosed tags
elsewhere in the file), the CLI (exit 0/1/2, folder
walking for several HTML files including `.htm`,
nested folders, `--no-recursive`, `--exclude`,
`.git` skipped, a direct file checked whatever its
name, duplicate paths checked once, `--json`
output, `--stdin`, bad flags, missing paths, empty
folders, `--version`, a non-UTF-8 file reported,
input files left unchanged, the tool run from
another folder and under a changed HOME), the
bundled examples (sample output compared byte-for-byte
against a fresh run, and the README-quoted outputs
checked against it), and hygiene checks (no
placeholder text, no absolute paths, no real secrets
outside the tests and examples, stdlib imports only,
no network use in the source, `.env` first in
`.gitignore`, CI file runs the test file, README
names the neighbouring repos).

## Contributing

Small, focused improvements are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT — see [LICENSE](LICENSE).

## Original work

This tool was written from scratch for this repo. The
idea of checking form actions is not new, and the
parsing follows Python's own standard-library HTML
parser — but no existing tool does this one job,
checking that every form in local HTML files carries
an action, as a tested command-line gate with a CI
exit code, as the search above shows — and every
line of code here is original, built on nothing but
Python's standard library.
