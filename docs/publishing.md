# Publication guide (GitHub)

**This is a candidate release, not evidence that an account/repository is already live.** Do not publish until you complete the manual approval gates below.

## Before making the repository public

- [ ] Confirm ownership and permission for *all* original text and scripts, including institutional/collaborator obligations.
- [ ] Audit every file in this repository, especially contributions and figures; verify licensing and attribution.
- [ ] Keep scientific projects and manuscript/reviewer material outside this source repository.
- [ ] Check that no sensitive data ever entered local Git history. Start with a **fresh** public repository if working from old private history.
- [ ] Run the following and inspect all outputs:

  ```bash
  python scripts/validate_skill.py .
  python scripts/check_release.py .
  python -m unittest discover -s tests -v
  ```

- [ ] Test actual Skill discovery and a simple invocation in the intended agent client.
- [ ] Manually inspect snippets and outputs for inadvertent details about unpublished projects.
- [ ] Enable secret scanning, push protection where available and private vulnerability reporting.

## Create the repository

1. On GitHub select **New repository** and name it `geophysical-research-workflow`.
2. For a clean upload, create an **empty** repository (do not initialize a second README or license on GitHub).
3. Upload all files *inside* the `geophysical-research-workflow` folder, including `.github/`, `.gitignore`, `.gitattributes`, `SKILL.md`, `LICENSE`, `scripts/`, `assets/`, and `references/`. Do not upload the ZIP as a single file.
4. For local Git, after rights approval:

   ```bash
   git init
   git add .
   git diff --cached --stat
   git diff --cached --check
   git commit -m "Release geophysical research workflow v1.1.0"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/geophysical-research-workflow.git
   git push -u origin main
   ```

5. Inspect GitHub Actions and the public file tree. Do not claim cloud CI is green before it runs.
6. Choose repository topics: `agent-skills`, `geophysics`, `scientific-workflows`, `research-reproducibility`, `python`.
7. Optional: after exercising the skill in a real agent environment, create a `v1.1.0` GitHub Release and attach the source ZIP.

The MIT license covers newly authored Skill content only. It grants **no rights** to underlying third-party geophysical observations, tomography, maps, manuscripts or research archives.
