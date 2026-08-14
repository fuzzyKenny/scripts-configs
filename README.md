# Scripts and Configs

Public dotfiles and utility scripts for a macOS development setup.

This repository is intended to be safe to publish: machine-local values such as names, emails, usernames, API keys, tokens, and secrets live outside git in `~/.env` or other ignored local files.

## What's included

- `configs/home/zshrc` — interactive Zsh configuration, aliases, completion, prompt setup, and local env loading
- `configs/git/gitconfig` — public Git config shell; identity is supplied from local environment variables
- `configs/starship/starship.toml` — Starship prompt configuration
- `configs/ghostty/config` — Ghostty terminal settings
- `configs/opencode/` — OpenCode configuration and plugin package files
- `configs/zed/settings.json` — Zed editor settings
- `scripts/bin/wallhaven-download.py` — Wallhaven wallpaper downloader
- `bin/install` — links repo files into the expected home-directory locations
- `bin/sync-from-home` — refreshes this repo from the live home-directory files

## Local secrets and identity

Create a local `.env` file in the repo root, or `~/.env` after installation. This file is ignored by git.

Example:

```sh
GIT_AUTHOR_NAME="Your Name"
GIT_AUTHOR_EMAIL="you@example.com"
GIT_COMMITTER_NAME="Your Name"
GIT_COMMITTER_EMAIL="you@example.com"
GITHUB_USER="your-github-user"

WALLHAVEN_API_KEY=""
```

The Zsh config sources `~/.env` automatically for interactive shells.

## Install

```sh
git clone git@github.com:YOUR_USER/YOUR_REPO.git ~/scripts-configs
cd ~/scripts-configs
./bin/install
```

`bin/install` creates symlinks from this repo into the usual config locations. Existing files are backed up under `~/.config-backups/<timestamp>/` before being replaced.

Linked locations include:

- `~/.zshrc`
- `~/.gitconfig`
- `~/.config/starship.toml`
- `~/.config/ghostty/config`
- `~/.config/opencode/`
- `~/.config/zed/settings.json`
- `~/bin/wallhaven-download.py`

If `.env` exists in the repo root, it is also linked to `~/.env`.

## Refresh from this Mac

After editing live config files directly, copy them back into the repo with:

```sh
./bin/sync-from-home
```

Review changes carefully before committing.

## Wallpaper downloader

```sh
wallhaven-download.py --limit 10 --query "nature"
```

The script uses the public Wallhaven API by default. Set `WALLHAVEN_API_KEY` in `~/.env` for authenticated results.

## Public repo safety checklist

Before pushing:

```sh
git status --short
git diff --staged
```

Do not commit:

- `.env` files
- API keys, tokens, cookies, or passwords
- SSH/private keys or certificates
- machine-specific private notes
- `*.local`, `secrets/`, or `private/` files

The `.gitignore` is configured to exclude common secret and local-only files.
