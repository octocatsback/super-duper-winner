# Super Duper Winner

Umbrella repository that collects every **public** GitHub project under [octocatsback](https://github.com/octocatsback) into one multi-folder tree (one subdirectory per source repo).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green.svg)](SECURITY.md)

This repository (`octocatsback/super-duper-winner`) is the umbrella itself and is not nested inside its own tree.

## How projects were imported

| Method | When it is used |
| ------ | --------------- |
| `git subtree add` / `git subtree pull` with `--squash` | Default for repos whose current tree fits in this umbrella |
| Shallow git submodule (`shallow = true` in [`.gitmodules`](.gitmodules)) | Enormous upstreams (`docs`, `node`) and `tryhackme` (push-protection) |

Subtree prefixes keep their original project files and licenses. Submodule prefixes are gitlinks: the blobs live in the source repository until you initialize the submodule.

### Initialize optional submodules

A normal clone does **not** download the large forks. To check one out locally:

```bash
git submodule update --init --depth 1 tryhackme   # small; room notes stay out of this repo's blobs
git submodule update --init --depth 1 docs        # ~2.3 GB upstream; shallow checkout
git submodule update --init --depth 1 node        # ~1.5 GB upstream; shallow checkout
```

### Refresh a vendored subtree

```bash
git subtree pull --prefix=<Directory> https://github.com/octocatsback/<repo>.git <branch> --squash
```

## Included projects

Public `octocatsback` repositories as of the import (GitHub user listing, 17 public repos).

| Directory | Source | Import | Ref |
| --------- | ------ | ------ | --- |
| [`About-Us/`](About-Us/) | [octocatsback/About-Us](https://github.com/octocatsback/About-Us) | squash subtree | `main` @ `7d4c49c` |
| [`adk-docs/`](adk-docs/) | [octocatsback/adk-docs](https://github.com/octocatsback/adk-docs) | squash subtree | `main` @ `1203686` |
| [`camo/`](camo/) | [octocatsback/camo](https://github.com/octocatsback/camo) | squash subtree | `master` @ `e59df56` |
| [`cli/`](cli/) | [octocatsback/cli](https://github.com/octocatsback/cli) | squash subtree | `latest` @ `c9876d7` |
| [`distributed-uncensorable-frontend/`](distributed-uncensorable-frontend/) | [octocatsback/distributed-uncensorable-frontend](https://github.com/octocatsback/distributed-uncensorable-frontend) | squash subtree | `main` @ `60938e3` |
| [`docs/`](docs/) | [octocatsback/docs](https://github.com/octocatsback/docs) | shallow submodule | `main` @ `8ace643` |
| [`Gareth/`](Gareth/) | [octocatsback/Gareth](https://github.com/octocatsback/Gareth) | squash subtree (refreshed) | default branch `cursor/lock-down-environment-7a39` @ `47066c2` |
| [`GitGoat/`](GitGoat/) | [octocatsback/GitGoat](https://github.com/octocatsback/GitGoat) | squash subtree (refreshed) | `main` @ `616ebbc` |
| [`hello-world/`](hello-world/) | [octocatsback/hello-world](https://github.com/octocatsback/hello-world) | squash subtree | `master` @ `1ea2de3` |
| [`node/`](node/) | [octocatsback/node](https://github.com/octocatsback/node) | shallow submodule | `main` @ `bbf51ad` |
| [`OriginTrials/`](OriginTrials/) | [octocatsback/OriginTrials](https://github.com/octocatsback/OriginTrials) | squash subtree (already current) | `gh-pages` @ `43e4684` |
| [`plugins/`](plugins/) | [octocatsback/plugins](https://github.com/octocatsback/plugins) | squash subtree | `main` @ `9bd4a82` |
| [`potential-octo-doodle/`](potential-octo-doodle/) | [octocatsback/potential-octo-doodle](https://github.com/octocatsback/potential-octo-doodle) | squash subtree | `main` @ `58a3ee1` |
| [`rumdl/`](rumdl/) | [octocatsback/rumdl](https://github.com/octocatsback/rumdl) | squash subtree | `main` @ `fd83c4b` |
| [`threat-finder/`](threat-finder/) | [octocatsback/threat-finder](https://github.com/octocatsback/threat-finder) | squash subtree | `main` @ `a81e069` |
| [`tryhackme/`](tryhackme/) | [octocatsback/tryhackme](https://github.com/octocatsback/tryhackme) | shallow submodule | `main` @ `3949051` |

`Gareth/`, `GitGoat/`, and `OriginTrials/` were already present from earlier work; they were refreshed in place rather than duplicated.

## Not copied as a nested project

| Repository | Reason |
| ---------- | ------ |
| [octocatsback/super-duper-winner](https://github.com/octocatsback/super-duper-winner) | This umbrella repository |
| [octocatsback/skills-agentic-workflows-that-read-the-room](https://github.com/octocatsback/skills-agentic-workflows-that-read-the-room) | Private; not part of the public-repo import |

## Fallback notes

- **`docs` and `node`**: GitHub reports ~2.3 GB and ~1.5 GB respectively. A full-history (or even a fully vendored HEAD) import would dominate this umbrella. They are pinned as shallow submodules so the projects are still present and updatable without silently omitting them.
- **`cli`**: Large (~179 MB git / ~334 MB working tree) but imported as a squash subtree of `latest`.
- **`tryhackme`**: Included as a submodule instead of a subtree because room notes contain AWS access-key-shaped strings (`AKIA…`) that GitHub push protection rejects when those blobs are committed here. Initialize the submodule to read the notes locally.

Umbrella build/docs are not required for every vendored tree. Open the subdirectory (or initialize the submodule) for the project you want.

## Getting started

```bash
git clone https://github.com/octocatsback/super-duper-winner.git
cd super-duper-winner
```

Open the subdirectory for the project you want to work on. Submodule prefixes stay empty until you run `git submodule update --init --depth 1 <name>`.

## Security

If you believe you have found a security vulnerability, follow [SECURITY.md](SECURITY.md). Do not open a public issue for security reports.

## License

The umbrella files in this repository (`LICENSE`, `README.md`, `SECURITY.md`) are under the [MIT License](LICENSE). Copyright (c) 2026 Gareth Kirman.

Project subdirectories remain under the licenses shipped with those projects.
