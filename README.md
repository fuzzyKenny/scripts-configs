# Scripts and configs

Personal scripts and configuration files.

## Layout

- `scripts/bin/` — executable scripts
- `configs/home/` — home-directory dotfiles without leading dots
- `configs/git/` — git config
- `configs/starship/` — Starship prompt config
- `configs/ghostty/` — Ghostty terminal config
- `configs/opencode/` — OpenCode config
- `configs/zed/` — Zed editor settings
- `bin/sync-from-home` — refresh this repo from the live home-directory files
- `bin/install` — symlink tracked files into the expected locations so this repo is the source of truth

## Refresh from this Mac

```sh
./bin/sync-from-home
```

## Install/link onto a Mac

```sh
./bin/install
```

This replaces the live files with symlinks into this repo. Existing files are backed up under `~/.config-backups/` first.

After that, edit files in this repo and the live config updates immediately.

Review files before committing. Do not commit API keys, SSH keys, tokens, or `*.local` files.
