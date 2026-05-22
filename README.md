# zlin1792.github.io

Personal academic website for Zhen Lin.

## Quality checks

Every pushed commit and every pull request runs a GitHub Actions workflow that checks for:

- site structure and website-specific content rules with `scripts/check_site.py`
- typos with `crate-ci/typos`
- broken links with `lychee`

Run the project-specific checks locally with:

```sh
python3 scripts/check_site.py
```
