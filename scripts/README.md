# History Builder

Rebuilds a research-milestone git timeline from the finished codebase using `commit-manifest.json`.

## Usage

```powershell
# Preview commit plan (no git changes)
.\scripts\build_research_history.ps1 -DryRun

# Rebuild master branch with backdated commits (destructive to current master)
.\scripts\build_research_history.ps1
```

## Design

- Commits follow portfolio build order: evaluation harness → RAG → V&V → reproducibility → MLOps → planning projects.
- Key Python modules use a two-phase shell-then-complete pattern for realistic churn.
- Timestamps use `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` between 2026-03-03 and 2026-08-31.
- `.gitignore` excludes virtualenvs, caches, and local assistant files.

## After rebuild

```powershell
git log --graph --oneline --date=short -20
git log --stat --oneline -5
```

To publish: `git push --force origin master` (only when you intend to replace remote history).
