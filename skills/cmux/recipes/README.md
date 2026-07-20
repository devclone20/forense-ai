# cmux Recipes

20 copy-paste, self-contained snippets for the cmux CLI + socket API. Each folder is one recipe. Each recipe has a 5-line `README.md` and a runnable `recipe.sh` (and a Python version where useful).

Browse the list:

| #  | Recipe                                                      |
|----|-------------------------------------------------------------|
| 01 | [notify-on-build-fail](./01-notify-on-build-fail)           |
| 02 | [flash-on-test-pass](./02-flash-on-test-pass)               |
| 03 | [screenshot-browser-surface](./03-screenshot-browser-surface) |
| 04 | [spawn-helper-pane](./04-spawn-helper-pane)                 |
| 05 | [send-text-to-other-surface](./05-send-text-to-other-surface) |
| 06 | [tail-vercel-deploy](./06-tail-vercel-deploy)               |
| 07 | [three-agents-on-pr](./07-three-agents-on-pr)               |
| 08 | [progress-bar-from-script](./08-progress-bar-from-script)   |
| 09 | [sidebar-status-pill](./09-sidebar-status-pill)             |
| 10 | [open-markdown-with-watch](./10-open-markdown-with-watch)   |
| 11 | [browser-fill-and-submit](./11-browser-fill-and-submit)     |
| 12 | [poll-socket-for-events](./12-poll-socket-for-events)       |
| 13 | [detect-cmux-context](./13-detect-cmux-context)             |
| 14 | [python-rpc-client](./14-python-rpc-client)                 |
| 15 | [batch-rename-workspaces](./15-batch-rename-workspaces)     |
| 16 | [auto-flash-on-stale-pr](./16-auto-flash-on-stale-pr)       |
| 17 | [ssh-remote-workspace](./17-ssh-remote-workspace)           |
| 18 | [browser-wait-for-element](./18-browser-wait-for-element)   |
| 19 | [agent-handoff-notification](./19-agent-handoff-notification) |
| 20 | [restore-session-on-boot](./20-restore-session-on-boot)     |

## Running a recipe

```bash
cd 01-notify-on-build-fail
chmod +x recipe.sh
./recipe.sh
```

Each recipe is independent and short. Read `recipe.sh` before running.

## License

MIT.
