# Public GitHub release: permission and privacy gates

This repository contains original workflow prompts, templates, basic validation scripts and **synthetic demonstration** only. It intentionally contains no archived project numerical arrays, journal PDFs, external maps/models, field photographs, confidential review records, identifiers or software API credentials.

Before publishing:

1. Confirm that you own or have rights to release the text and code, including institutional/project coauthor and employer obligations. Public availability of scientific data does **not** automatically mean redistribution is permitted.
2. Do not blindly upload archived research ZIPs, directories or manuscript drafts; review licensing for WGM2012, XGM2019e/GOCE, ETOPO, seismological and Moho sources, and maps **for each version and provider**. Link official download sources rather than mirroring without permission.
3. Search tracked files and git history for tokens/keys/passwords (`.env`, cloud access keys), personal phone/email/addresses, field GPS coordinates where sensitive, internal approvals, grant/payment information, collaborator messages and private reviewer reports. Rotate any credential found; deleting latest file does not remove git history.
4. Check every image, font, paper figure and code dependency licensing and attribution. Do not bundle external font files.
5. For scientific claims in README, disclose whether evidence is reproduced in the release. This open skill is a workflow, **not** a publication of the historical numerical result or proof of real-world predictive performance.
6. Run `python scripts/check_release.py .`; manually inspect flagged items and run GitHub secret scanning. Automated scanning is incomplete.
7. Use a clean first public commit from the curated directory. Do not initialize the public repo by importing prior private git history.

The MIT license here applies only to original material in this skill package. It does not relicense underlying research datasets or articles. If contributors' rights cannot be confirmed, postpone publication and use a private repository instead.
