# Contributing to LFFA

Thanks for helping improve the Local-First Financial Agent. This project targets hackathon judges and developers who want a **small, honest** local-first agent scaffold — keep PRs focused and well tested.

## Development setup

```bash
git clone https://github.com/ennydev-2026/local-first-financial-agent.git
cd local-first-financial-agent
pip install -e ".[dev]"
cp .env.example .env
```

Run tests:

```bash
python3 -m pytest
```

After changing environment handling, call `lffa.config.reset_config_cache()` in tests that patch `os.environ`.

## Branch and commit conventions

- Branch from `main` (e.g. `feature/my-change-9f87` or your team’s naming).
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Reference GitLab/GitHub issues in the commit body when applicable (`#123`).

## Pull requests

- One logical change per PR when possible.
- Update docs if CLI, env vars, or stub vs real behavior changes.
- Ensure `python3 -m pytest` passes.
- Describe **what works** vs **what remains stubbed** — judges read the README first.

## Adding a backend

### Local SLM

1. Read `slm.LocalSlmBackend` protocol in `src/lffa/slm.py`.
2. Implement `complete(prompt) -> SlmCompletion`.
3. Wire into `complete_local()` with clear fallback and stderr notices.
4. Document new env vars in `.env.example` and `config.py`.
5. Add unit tests with `urllib` or backend mocks — no live Ollama required in CI.

### Overflow (Nosana or other)

1. Extend `nosana_overflow.submit_overflow_job()` or add a sibling module.
2. Keep **stub fallback** when keys are missing; never raise to the CLI for network errors.
3. Log backend choice via `NosanaSubmitResult.backend` (`nosana` | `stub`).
4. Update `docs/nosana-credits.md` if credit-consuming behavior changes.

### Provenance

1. Extend `arweave_provenance.upload_artifact()` — do not return fake `tx_id`.
2. Add tests for new status strings.

## Code style

- Stdlib first; justify new dependencies in the PR and `pyproject.toml`.
- Match existing module layout under `src/lffa/`.
- Prefer explicit types and small dataclasses over heavy frameworks.

## Questions

Open an issue with context (hackathon submission, local SLM setup, Nosana credits). For security-sensitive reports, avoid pasting API keys in public issues.
