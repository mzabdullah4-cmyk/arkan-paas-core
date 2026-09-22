# Arkan status CLI

The repository includes `scripts/arkan-status.py`, a dependency-light CLI that checks:

- Git branch and working-tree status
- Docker Compose service status
- portal reachability
- control-plane `/health` reachability

Run it from a checkout:

```bash
python3 scripts/arkan-status.py
python3 scripts/arkan-status.py --url http://VM_IP:8080 --api-url http://VM_IP:8000 --json
```

The control-plane port should remain private in production; normally check the API through the portal/reverse proxy instead.

## GitHub CLI

Yes. GitHub provides the open-source `gh` command-line tool for repositories, issues, pull requests, Actions, releases, and API access. Install it from the official [GitHub CLI installation instructions](https://github.com/cli/cli#installation), then authenticate with:

```bash
gh auth login
gh repo view mzabdullah4-cmyk/arkan-paas-core
gh run list --repo mzabdullah4-cmyk/arkan-paas-core
gh issue list --repo mzabdullah4-cmyk/arkan-paas-core
gh pr list --repo mzabdullah4-cmyk/arkan-paas-core
```

`gh` checks GitHub state; `arkan-status.py` checks the checked-out app and its running services.
