# Contributing

Keep the core standard-library only and passive. Changes should include a reproducible failing case and a focused test when behavior changes. Run `python3 -m unittest discover -s tests -v` and both documented example commands before submitting.

Use fictional domains and cases in fixtures. Do not attach account cookies, tokens, customer identifiers, private screenshots or production ledgers. Report gaps and unknown outcomes explicitly. Avoid keyword-only sentiment scoring or automatic incident closure.

Document observable behavior and limitations. A test passing does not prove live browser compatibility or platform coverage. Preserve `skill/` relative links and the installer's no-overwrite guarantee.
