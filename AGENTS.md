# Brighton Lanes Bot

Reddit bot u/BrightonLanesBot. It watches new posts and comments on r/brighton. When the text contains a trigger word, it replies with the difference between The Lanes and North Laine.

The bot posts public replies. Get Kristian's approval before you deploy a change to the trigger words, the reply message, or the subreddit.

## Stack

- Python 3.13 and PRAW 7.8.1, pinned in `requirements.txt`. PRAW 8.x is untested with this script.
- One file: `brighton_botv2.py`. It runs two threads (a post stream and a comment stream). The main loop restarts a thread that stops.
- Docker Compose on the VPS. The bot has no inbound traffic, so it has no ports and no Traefik labels.

## Paths

| Thing            | Location                                             |
|------------------|------------------------------------------------------|
| Source (Mac)     | `/Users/kristian/Claudey/brighton-bot`               |
| Live copy (VPS)  | `/docker/brighton-bot` on SSH host `dott-vps`        |
| Container        | `brighton-bot`                                       |
| Credentials      | `/docker/brighton-bot/data/praw.ini`, VPS only       |
| Replied-to IDs   | `/docker/brighton-bot/data/replied_to.txt`, VPS only |

## Configuration

- `SUBREDDIT_TO_MONITOR`, `TRIGGER_WORDS` and `REPLY_MESSAGE` are constants at the top of `brighton_botv2.py`.
- The working directory in the container is `/data`. The script reads `praw.ini` (section `[bot1]`) and `replied_to.txt` from the working directory.
- `praw.ini` holds the Reddit client ID, client secret, username and password. Its mode is 600. Never print its values and never copy it into this repo. `data/` is in `.gitignore` and `.dockerignore`.

## Deploy

Run both commands from the repo root. The first command leaves `data/` on the VPS untouched.

```bash
rsync -rlpt --exclude data/ --exclude .git/ --exclude __pycache__/ --exclude .DS_Store ./ dott-vps:/docker/brighton-bot/
ssh dott-vps 'cd /docker/brighton-bot && docker compose up -d --build'
```

## Check

```bash
ssh dott-vps 'docker ps --filter name=brighton-bot && docker logs --tail 30 brighton-bot'
```

A healthy start prints `Successfully connected as user: BrightonLanesBot`, then the count of replied-to IDs.

## Gotchas

- Do not use `rsync -a` to the VPS. It keeps the Mac user ID (501) on the files. Use `-rlpt` so root owns them.
- Docker does not run on the Mac. The build on the VPS is the first build test.
- There are no tests and no linter. Before a deploy, check the syntax: `uv run --no-project --python 3.13 --with praw==7.8.1 python -m py_compile brighton_botv2.py`.
- The streams use `skip_existing=True`. The bot sees only posts and comments made after it starts.
- The bot prints one or more lines for every new post and comment. Compose caps the logs at 3 files of 5 MB.
- After a failed login, the script waits 60 seconds before the next try. Keep that wait: without it, a bad password causes non-stop login requests.
