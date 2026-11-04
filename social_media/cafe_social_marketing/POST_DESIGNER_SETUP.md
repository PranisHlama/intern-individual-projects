# Post Designer (20.0.6.1.0)

This release builds on the Instagram v9 addon (20.0.6.0.0). It adds a browser
editor; it does not require an AI model, npm installation, or a new account.
Keep your existing platform settings. This archive does not include TikTok v10.

## Upgrade an existing v9 test instance

Back up the addon and the Odoo database/filestore before upgrading. If you
already installed a different addon version or made local changes, compare
the source first. Do not overwrite those changes with this archive.

Unzip into a new folder. Copy the included cafe_social_marketing directory
into the existing addons location. Upgrade Cafe Social Marketing on the
same database after stopping the regular Odoo server process; then restart
the service. On the previously used Mac Docker Compose setup, from the
compose directory with PostgreSQL running:

```sh
docker stop odoo20
docker compose run --rm --no-deps odoo odoo -d Mailintegration \
  -u cafe_social_marketing --stop-after-init --no-http
# Only restart once the upgrade succeeds:
docker compose up -d --no-deps odoo
```

Keep other addons intact. The first load may rebuild backend assets.

## Smoke test

1. Save a fresh draft social post and click **Design Image**.
2. Add a background, text and a logo, then drag and resize a layer.
3. Click **Save JPEG to post**. Confirm the draft has one JPEG and that
   opening the designer again restores the editable layers.
4. Confirm another media attachment requires explicit replacement. Old files
   are detached from the publication selection; the editor does not delete
   them from Odoo.
5. Approve a draft, save a changed design, then confirm that validation and
   approval reset. Resubmit before publication.
6. Check that scheduled or published posts cannot open or save designs.
   Try saving two editors for the same draft; the stale one should be rejected.
7. On a fresh approved demo record, test the normal Facebook or Instagram
   publish action. Instagram still hosts the approved JPEG through Cloudinary.

The editor exports the canvas preview, excluding the selection outline.
It stores uploaded sources in the editable document. Start with smaller
JPEG/PNG files and keep the editable document under 7 MiB. This build has
offline checks; the live Odoo registry, asset bundle and publication still
need to be tested in your environment.
