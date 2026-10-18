# Contributing

Thanks for helping improve this workflow. Small, auditable changes are preferred over a large speculative feature set.

## Before opening a pull request

1. Open an issue describing the problem or proposed improvement. For a security concern, follow [SECURITY.md](SECURITY.md), not a public issue.
2. Keep examples synthetic and openly redistributable. **Do not contribute** unpublished data, manuscript/reviewer correspondence, personal identifiers, access tokens, field locations, copyrighted maps or model files.
3. Explain the affected research/validation gate and limits of the proposed change. Do not weaken warnings just to make a test pass.
4. Run:

   ```bash
   python scripts/validate_skill.py .
   python scripts/check_release.py .
   python -m unittest discover -s tests -v
   ```
5. Add tests for every changed validator behavior. Document breaking schema changes and migration paths.

By submitting a contribution, you represent that you have the rights needed to license that contribution under this repository's MIT license. Maintainers may request a separate permission review where institutional or project agreements apply.
