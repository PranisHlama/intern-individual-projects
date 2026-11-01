# Facebook Publishing Attempt History

Status: Draft — review before implementation
Created: 2026-10-28

## Problem

The current addon records only the latest Facebook publishing result.
Users cannot inspect previous attempts after those fields change.

## Goal

Allow authorised marketing staff to inspect a chronological history of
Facebook publishing attempts without changing publishing eligibility,
approval rules, or existing scheduling behaviour.

## User Stories

1. As a Marketing User, I can inspect attempt history for posts I can access.
2. As a Marketing Manager, I can distinguish confirmed success, confirmed
   failure, and an uncertain publishing outcome.
3. As a reviewer, I can identify when an attempt occurred and which Facebook
   account and Page it targeted.

## Requirements

FR-001: Record one history entry for each publishing operation that passes
preflight and invokes the Facebook publishing service. Scheduling a post
alone MUST NOT create an attempt.

FR-002: Each entry records the post, social account, target Page ID,
start time, completion time, executing Odoo user, and outcome.

FR-003: Outcomes distinguish In Progress, Published, Failed, and Unknown.
Published requires the remote identifiers already required by the adapter.

FR-004: Store confirmed remote identifiers and a safe error summary when
available. Never store tokens, request headers, raw API responses, image
bytes, or the full caption in attempt history.

FR-005: Preserve existing latest-result fields and publishing behaviour.
Unknown outcomes MUST continue to block further publishing.

FR-006: Display history newest first on the post form, including a clear
empty state when no attempts exist.

FR-007: Users can read history only for posts they are authorised to access.
Marketing Users and Managers cannot manually create, edit, or delete entries,
including through RPC. History is maintained by the publishing workflow.

FR-008: Record handled API failures without raising a new exception that
rolls back the failure history.

FR-009: Both manual and scheduled publishing use this history mechanism.
Local validation failures before service invocation are not API attempts.

FR-010: Existing post-level locking MUST continue to prevent concurrent
publishing requests from sending an already-confirmed post again.

## Acceptance Criteria

AC-001: A successful text publication creates one Published entry with its
confirmed remote post ID and leaves the post Published.

AC-002: A successful photo publication records the confirmed post and photo IDs.

AC-003: A handled API rejection creates a Failed entry with a safe error summary
and preserves the adapter's existing failure behaviour.

AC-004: A timeout or missing required remote ID creates an Unknown entry.
A subsequent publish request is blocked without creating another API attempt.

AC-005: An unapproved or non-compliant post makes no Facebook request and
creates no attempt entry.

AC-006: Scheduling creates no entry; execution by the scheduler creates one
when it invokes the publishing service.

AC-007: A later permitted attempt creates a new entry without modifying
the completed earlier entry.

AC-008: Direct user attempts to create, edit, or delete history are denied.
Users without access to a post cannot read its attempt history.

AC-009: Opening history makes no publishing request.

AC-010: Relevant existing approval, scheduling, text publishing, and photo
publishing checks continue to pass.

## Exclusions and Limitations

No retry button, automatic retries, token refresh, additional platforms,
Facebook video publishing, or reconciliation interface.

No historical entries will be invented for publications made before this
feature is installed.

This feature does not guarantee durable history across process crashes or
database transaction rollbacks. It does not solve the existing possibility
of remote success followed by local transaction failure.

## Verification

Use mocked API responses for success, rejection, timeout, and missing IDs.
Verify access rules and workflow behaviour in an Odoo runtime.
Report live Facebook testing separately; do not publish during automated tests.

## Open Review Decisions

- Decide whether posts with attempt history can be deleted or must be archived.
- Confirm how deleted or archived social accounts are represented in history.

## Clarification Decisions — 2026-10-28

FR-011: Prevent deletion of posts with publishing attempt history.
Adding post archiving is outside this feature's scope.

FR-012: Prevent deletion of social accounts referenced by publishing attempts.
Preserve any existing archive or deactivation behaviour.

FR-013: Store the target Page ID as a snapshot on each attempt. Later changes
to the social account MUST NOT alter completed history entries.

AC-011: Deleting a post or social account referenced by an attempt is blocked
with a clear explanation.

AC-012: Changing an account's configured Page ID leaves earlier attempt
Page IDs unchanged.

These decisions resolve the two questions in Open Review Decisions.
