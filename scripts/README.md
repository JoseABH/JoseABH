# Profile cards

Run `python scripts/generate-profile-cards.py` from the repository root to refresh
the SVGs in `assets/generated`. Python 3.13 and the standard library are enough.
`GITHUB_TOKEN` is optional locally; the daily workflow uses the built-in Actions
token, without a personal access token or external rendering service.

The overview counts public, non-fork repositories, their stars and forks, and
the profile's followers. The language chart counts each repository's primary
language, excluding forks and repositories without a detected language. It does
not measure code volume, commits, or skill. Milestones are public profile totals,
not GitHub's official achievement badges; the README links to those separately.

API errors stop generation before replacing existing cards. The workflow commits
only successful updates and runs daily or through **Run workflow** after these
files reach the default branch. Branch rules must allow the workflow's commits.

Validation: `python -B -m unittest discover -s scripts -p "test_*.py"`.
