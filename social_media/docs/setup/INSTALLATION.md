# Installation and environment configuration

This repository contains an Odoo addon, not a standalone server or a complete Docker deployment. Use Odoo 20 Community and PostgreSQL with an existing addons mount. The module depends on `base`, `mail` and `product`; Python imports include `requests` and Pillow (`PIL` in the manifest), plus dependencies supplied by Odoo.

## Deployment example

The owner's existing setup uses host `~/Desktop/odoo20`, Compose services `odoo` and `db`, containers `odoo20` and `odoo20-db`, database `Mailintegration`, and browser address `http://localhost:8000`. The host addon directory is mounted at `/mnt/extra-addons`. These are examples, not universal defaults.

Check the service names and mount paths without displaying credential values:

```bash
cd ~/Desktop/odoo20
docker compose config --services
docker inspect odoo20 --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

The addon must be on Odoo's configured addons path. Do not replace other addons or use a source archive as a replacement for the entire Compose project.

## Back up before installing/upgrading

Back up the database, addon and required filestore consistently before changing an existing instance. A `pg_dump` is not a filestore backup; the latter contains attachment files and needs its own deployment-appropriate backup/restore procedure.

Example addon/database snapshot, with PostgreSQL running and the regular Odoo service stopped:

```bash
cd ~/Desktop/odoo20
docker compose stop odoo
backup_dir="$HOME/Desktop/odoo-addon-backups/manual-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
cp -R "$HOME/Desktop/odoo20/addons/cafe_social_marketing" "$backup_dir/"
docker exec odoo20-db pg_dump -U odoo -Fc Mailintegration > "$backup_dir/Mailintegration.dump"
```

Check the dump command succeeded and the file is nonempty before proceeding. Protect backups because they may contain private data. Do not commit dumps, filestore data, passwords or tokens.

## Copy and install the addon

From the project's `social_media/` directory, copy the reviewed addon to the existing host addons location, for example:

```bash
rsync -av --exclude='__pycache__/' --exclude='*.pyc' \
  ./cafe_social_marketing/ \
  "$HOME/Desktop/odoo20/addons/cafe_social_marketing/"
```

For a fresh database, start Odoo, update the Apps list and install **Cafe Social Marketing**. For an existing installation, keep normal Odoo stopped and run the upgrade before restarting:

```bash
cd ~/Desktop/odoo20
docker compose run --rm --no-deps odoo \
  odoo -d Mailintegration -u cafe_social_marketing --stop-after-init --no-http \
  && docker compose up -d odoo
```

A failed upgrade should leave the normal service stopped for investigation. Do not ignore a traceback and restart as if the schema were upgraded. New stored fields require an upgrade; restart alone can cause `UndefinedColumn`. Pure frontend/Python edits without schema changes generally need a restart and browser refresh rather than a model upgrade.

The first page load may rebuild backend assets. Hard-refresh with Cmd+Shift+R on Mac if the old Designer UI remains. Do not delete arbitrary assets or database records as a first troubleshooting step.

## Inject existing credentials

Use one private env file already referenced by the Odoo service, or add a new one without replacing existing configuration. Example `facebook.env` contents use placeholders only:

```dotenv
CAFE_FB_PAGE_TOKEN=YOUR_FACEBOOK_PAGE_TOKEN
CAFE_IG_ACCESS_TOKEN=YOUR_INSTAGRAM_TOKEN
CAFE_CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME
CAFE_CLOUDINARY_API_KEY=YOUR_API_KEY
CAFE_CLOUDINARY_API_SECRET=YOUR_API_SECRET
```

Under the **existing Odoo service** in Compose, append the file to `env_file`:

```yaml
env_file:
  - ./facebook.env
```

Preserve existing DB credentials, ports, volumes and env files. Compose's interpolation `.env` does not inject values by itself; explicit `environment` mappings or `env_file` are needed. Environment changes require container recreation, not just restart:

```bash
cd ~/Desktop/odoo20
chmod 600 facebook.env
docker compose up -d --no-deps --force-recreate odoo
```

Presence-only check (never prints values):

```bash
docker exec odoo20 python3 -c 'import os; keys=("CAFE_FB_PAGE_TOKEN","CAFE_IG_ACCESS_TOKEN","CAFE_CLOUDINARY_CLOUD_NAME","CAFE_CLOUDINARY_API_KEY","CAFE_CLOUDINARY_API_SECRET"); print({key: bool(os.getenv(key)) for key in keys})'
```

A True value confirms presence only, not validity or permissions. Actual secrets remain readable to Docker administrators; this is a development credential arrangement, not an OAuth renewal or production secret-management system.

## Configure users and records

Assign Marketing User/Marketing Manager roles through the existing Odoo user permissions. Managers imply Users. Create branches, platform accounts, valid campaigns and test posts. The account picker opens ordinary setup forms. Use platform-specific numeric IDs and token **variable names**, never a token in the variable-name field.

Follow [Facebook](FACEBOOK_SETUP.md), [Instagram](INSTAGRAM_SETUP.md), [Profile sync](PROFILE_SYNC_SETUP.md) and the [manual verification checklist](../reference/VERIFICATION.md). Optional [AI Review](AI_REVIEW_SETUP.md) is independent of publishing/Designer.

## Boundaries

No tunnel is needed for Facebook publishing, Cloudinary-backed Instagram publishing or profile sync. Legacy external-image hosting is a separate case. Meta OAuth is absent from this snapshot; old `CAFE_META_...` settings do not enable it. Do not install previously prepared OAuth files as part of this setup.

The project has no committed Compose stack or automated tests in the reviewed archive. Do not assume an untracked local deployment or a previous release-package test folder is included in a fresh clone.
