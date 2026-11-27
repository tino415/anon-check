# AGENTS.md

`anon-check` reads text on stdin and reports personal data by position (`line:col len TYPE score`), never by value, or masks it with typed tokens (`--mask`). `--csv` does the same per cell. Exit 0 clean, 1 findings, 2 error.

## Layout

- `src/anon_check/`: the filter; rules in `rules.py`, the model adapters in `models.py`
- `bin/anon-check`: the podman wrapper, no network, read-only, no capabilities
- `bin/anon-check-build`: builds the image with the first model of `models.tsv`; the only step with network
- `bin/eval`: builds an image per candidate in `models.tsv` and prints its recall per language
- `nix/anon-check.nix`: the package that puts both commands on PATH

## Rules

- The gate is `bin/test`; there is no CI. Report its result as `gate passed at <sha>`.
- The repo holds only synthetic data. Never commit a real name, number or document, not even in a test.
- Output never carries a found value, on stdout or stderr.
- No Presidio and no spaCy in the image.
- Say a model's weight size before downloading it; nothing over 1 GB without the owner's yes.
