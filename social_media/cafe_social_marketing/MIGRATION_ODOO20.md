# Odoo 20 Migration Notes

This module targets Odoo 20.0.

Key migration changes applied:

- Manifest version updated to `20.0.1.0.0`.
- Odoo 20 security migration applied: legacy `ir.model.access` / `ir.rule` access definitions were replaced by unified `ir.access` data.
- `security/ir.model.access.csv` was replaced with `security/ir.access.csv` using the Odoo 20 schema:
  `id,name,model_id,group_id/id,operation,domain`.
- User access uses `cru` (create, read, update) and manager access uses `crud`.
- Existing Marketing User / Marketing Manager privilege setup retained.
- Existing Odoo models, views, cron, approval workflow and AI/Ollama integration retained.

External social-platform publishing remains a planned integration.
