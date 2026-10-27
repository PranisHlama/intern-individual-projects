# Odoo Individual Projects

One shared repository with a separate branch for each individual project.
The `main` branch contains only this README.

| Individual project | Project branch | Project directory on that branch |
| --- | --- | --- |
| AI_MCP | `AI_MCP` | `AI_MCP/` |
| DMS | `DMS` | `DMS/` |
| IOT | `IOT` | `IOT/` |
| MIS | `MIS` | `MIS/` |
| Survey | `Survey` | `Survey/` |
| social_media | `social_media` | `social_media/` |

Each project branch contains this guide and only its own project directory.
Switching branches changes which project directory is present in your checkout.
Commit or stash your work before switching branches.

## Start working

Once this repository has been published, clone it and switch to your project
branch. For example, for the DMS project:

```sh
git clone <repository-url> odoo-individual-projects
cd odoo-individual-projects
git switch DMS
git pull --ff-only origin DMS
git switch -c DMS/short-description
```

Use your project's branch name in place of `DMS`. Put project files inside
that project's directory. Use a unique feature branch name for each change.

```sh
git add DMS/
git commit -m "Describe the change"
git push -u origin DMS/short-description
```

Open a pull request with your project branch (for example, `DMS`) as the base.
Keep project changes on their project branches so `main` stays README-only.
Before starting another change, switch to your project branch and pull its latest
changes, then create a new feature branch.

Keep passwords, tokens, and local `.env` files out of Git. Use `.env.example`
with placeholder values to document required configuration.

## Initial publishing

After creating an empty remote repository, publish all seven branches:

```sh
git remote add origin <repository-url>
git push -u origin main AI_MCP DMS IOT MIS Survey social_media
```

Set `main` as the default branch on the hosting service. Contributors need write
access to the shared repository to push their feature branches.
