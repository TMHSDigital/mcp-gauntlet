## What this changes

<!-- One or two sentences. Link the issue: "Fixes #123". -->

## How it was checked

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `ruff check .` and `mypy` pass
- [ ] `CHANGELOG.md` has an entry under "Unreleased" if users will notice the change

## For a new or changed scenario

- [ ] The payload asks only for something inert and observable
- [ ] The server still opens no file other than its log and makes no network connection
- [ ] Nothing an agent sends is written to the log (sizes and names only)
- [ ] Tests include an agent that obeys the payload and one that only does the task
- [ ] The README scenario table and the site are updated
