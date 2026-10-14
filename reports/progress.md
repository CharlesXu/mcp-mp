# Implementation ledger — plan: docs/superpowers/plans/2026-10-14-mcp-marketplace.md

Ruling: New independent repository is the isolated workspace; no linked worktree is needed for an unborn repository. Creation and first main publication are explicitly authorized by the user.
Ruling: No draft PR for an empty repository bootstrap; publish the validated initial main branch as requested.
Pre-flight: Tasks 1→2→3→4 share normalized entry fields; schema is authoritative. Task 5 writes protocol evidence separately; Task 6 publishes only sanitized outputs.
Task 1: RED observed missing normalize; GREEN: 8 import boundary tests passed. Inventory read-only import: 278 unique entries.
Ruling: All local launch definitions require separate version/command review; no automatic stdio candidate export from imported WorkBuddy launchers. Native catalog MCP itself will provide tested stdio support.
Ruling: Use current official SDK 2.3.0 and Client API instead of the plan's v1 ClientSession wording; current documentation establishes Client lifecycle and typed snake_case results.
Task 2: RED missing build/validate; GREEN: 14 total tests passed; 278 entries and self-contained plugin catalogue generated; publication structure checks passed.
Task 1 follow-up: scanner caught internal domains in original inventory descriptions. Added failing regression, removed domain text, reimported and verified GREEN before any data commit.
Task 3: RED missing adapter; GREEN: 20 total tests passed. Codex TOML/header environment mapping, Claude http/sse and Cherry streamableHttp/sse templates parse correctly.
Ruling: Codex dynamic URL parameters and unresolved stdio placeholders cannot be installed directly; adapter refuses them instead of pretending Codex expands those strings. Cherry placeholders require manual filling before import.
