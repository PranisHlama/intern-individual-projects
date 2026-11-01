# Cafe Social Marketing Constitution

## Core Principles

### I. Deterministic Business Validation
Odoo MUST enforce campaign dates, branch and account relationships,
discount accuracy, and publishing eligibility through deterministic rules.
AI output MUST NOT override these rules.

### II. Human Approval
Publishing MUST require current manager approval and successful compliance
validation. Changes to approval-relevant content MUST invalidate prior
approval and validation. AI review is advisory.

### III. Server-Side Permissions
Protected actions and workflow transitions MUST enforce permissions in
Python. Hidden buttons and read-only interface fields are not sufficient
security controls.

### IV. Credential Protection
Real tokens, passwords, and secrets MUST NOT enter Git, specifications,
logs, or user-facing errors. Configuration examples MUST use placeholders.
External API calls MUST use appropriate authentication and timeouts.

### V. Accurate Publishing Results
A post MUST NOT be marked Published without a successful platform response
and the required remote identifier. Uncertain outcomes MUST be distinguished
from confirmed failures. Retries MUST account for duplicate-publishing risk.

### VI. Specification Before Implementation
Every new feature or behaviour change MUST have reviewed requirements,
acceptance criteria, permissions, failure scenarios, and explicit exclusions
before implementation. Plans and tasks MUST remain consistent with the spec.

### VII. Evidence-Based Verification
Changes MUST be checked against their acceptance criteria, including relevant
success, failure, and permission scenarios. Reports MUST distinguish static
checks, mocked tests, Odoo runtime tests, and live platform tests.
Unexecuted tests MUST NOT be reported as passed.

### VIII. Maintainable Odoo Implementation
Use Odoo 20 Community conventions and existing module structure.
Keep business workflow in models and platform communication in services.
Keep the interface simple. Changes MUST check relevant existing workflows,
especially Facebook publishing, scheduling, compliance, and approvals.

### IX. Honest Scope and Efficient AI Use
Document implemented, partially implemented, and planned features separately.
Existing functionality documented after implementation MUST be identified
as a baseline, not presented as evidence of earlier spec-driven development.
Provide AI with relevant files and concise context. Review generated changes.
Prefer suitable open-source tools and document exceptions when needed.

## Project Boundaries

The application is the cafe_social_marketing addon for a multi-branch cafe.
Odoo manages business workflow, local AI assists content review, and external
platform APIs perform actual publishing.

Project files belong within social_media/ in the shared repository.
Credentials and machine-specific settings remain local.
Installing Spec Kit does not establish that existing code satisfies these rules;
gaps MUST be recorded and prioritised.

## Development Workflow

1. Inspect relevant existing code and identify the intended change.
2. Write the specification and measurable acceptance criteria.
3. Resolve material ambiguities and review the specification.
4. Write an implementation plan and ordered tasks.
5. Implement the scoped change and verify its acceptance criteria.
6. Record results, limitations, and remaining work.
7. Commit reviewed changes on a feature branch and open a pull request
   targeting social_media. Keep main README-only.

Specifications, plans, tasks, and verification evidence MUST be updated when
requirements change. Keep changes focused and avoid unrelated refactoring.

## Governance

This constitution governs future development of this project.
Amendments MUST record their reason and effect on existing specifications.

Use semantic versioning: major for incompatible principle changes, minor
for new principles, and patch for wording clarifications.

Each change review MUST check applicable principles. Exceptions MUST include
a reason, impact, and follow-up action, and require project-maintainer agreement.
Review temporary amendment notes before committing.

**Version**: 1.0.0 | **Ratified**: 2026-10-28 | **Last Amended**: 2026-10-28
