# Security Policy

This tool runs locally, collects no data, sends nothing anywhere, and needs no API key or secret. It only reads the HTML files you point it at, and it never rewrites a file and never changes anything. It writes nothing except the report on standard output (and usage errors on standard error). It never fetches a URL: an `action` address is checked for being there, not opened.

It only checks that a form carries an action attribute. It never submits a form, never loads a page, and never runs JavaScript.

If you find a case where the tool rewrites a file, opens a URL, or reports a pass for an HTML file with a form that has no action, please open an issue describing the exact commands and input. Do not include any real secret in the report.
