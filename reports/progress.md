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
Task 4: RED missing server, then untyped structured-output return surfaced in real SDK tests; GREEN after typing dict[str, Any]. Real stdio test covers all 278 records, lookup/export/errors and an independently copied plugin.
Task 4 native verification: Codex 0.162.1 and Claude Code 2.1.251 successfully added the local marketplace and installed/read back the enabled plugin in fresh isolated config homes. Installed launchers passed SDK handshake and search. No user client configuration was changed.
Task 5: RED missing probe, then 401 handling failed because SDK wraps transport errors. Added status observation without storing response content; GREEN: timeout, 401, HTML 200, pagination, mismatched ID and policy checks pass.
Ruling: Remote DNS resolves to non-global 198.18.* on this host. Do not relax the public-address guard or change user networking. Four explicit probes are marked skipped/network-policy-blocked, not service failures. Earlier generic error observations retained in report history.
Task 6 implementation: Documentation, rights/source notice, client config generator and Linux Python 3.11/3.13 offline CI prepared. Initial 31-test run had one macOS symlink-alias path assertion failure; see correction below. Strict Claude marketplace/plugin manifest validation passed. Deterministic build and publication structure checks passed.
Ruling: Add a local-clone catalog config generator so Cherry can connect to the same actual directory MCP rather than receiving only downstream templates. It prints configuration and leaves client files unchanged; paths with spaces are covered by a failing-then-passing test.

Task 6 verification correction: macOS temporary path is /var aliasing /private/var. Compared resolved paths without changing the production generator; full 31-test suite now passed. Shell verification uses fail-fast before committing subsequent work.
Task 6 pre-publication: Python 3.11 and 3.13 each passed the full 31-test suite. Strict Claude manifest validation and deterministic build passed. Public tracked-file scan passed after excluding a public connector ID from a credential-value false positive. Independent whole-repository review dispatched read-only as required by executing-plans; no implementation work delegated.
