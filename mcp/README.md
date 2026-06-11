# MasterBrain MCP Server (Phase 3b)

A **pure thin client**: every tool call is forwarded to the authenticated
MasterBrain HTTP API on the Unraid box. This process holds no policy, reads
no vault files, and imports nothing from the `app/` package. If the API
rejects a call (wrong identity, non-draft claim, unknown subject, privileged
edge type, oversize payload), the tool returns the API's reason verbatim.

## The contract (enforced by the API, not negotiable here)

- You write as the agent your token belongs to. Spoofing is rejected.
- Notes land only in your own `inbox/<agent>/` lane, as `draft`.
- Claims are always `draft`. Only Clint elevates, via the local CLI.
- `approved_by` / `supersedes` edges and ALL review/approve/reject/link/
  supersede/canonical operations do not exist over this transport.
- Every write attempt is audit-logged on the server.
- LAN-only. Never expose the API or this config to the internet.

## Setup (per agent - never share tokens between agents)

```bash
pip install -r mcp/requirements.txt
```

Claude Code / Cowork `.mcp.json` entry (any stdio-capable harness is
equivalent):

```json
{
  "mcpServers": {
    "masterbrain": {
      "command": "python",
      "args": ["/path/to/masterbrain-code/mcp/masterbrain_mcp.py"],
      "env": {
        "MASTERBRAIN_API_URL": "http://<unraid-lan-ip>:8077",
        "MASTERBRAIN_TOKEN": "<PASTE-TOKEN-HERE>"
      }
    }
  }
}
```

Get a token from Clint (`masterbrain token issue --agent <you>`, shown once).
Keep it in this env block or a local secrets manager - **never** commit it,
never paste it into the vault, chats, or notes. Revocation is instant:
`docker exec masterbrain python -m masterbrain token revoke --agent <you>`.

## Tools

Writes: `masterbrain_add_note`, `masterbrain_add_claim` (draft-only;
`force_new_subject` only for genuinely new subjects - audited),
`masterbrain_add_source`, `masterbrain_add_edge` (provenance types only).
Reads: `masterbrain_stats`, `masterbrain_list_claims`,
`masterbrain_get_claim`, `masterbrain_list_sources`,
`masterbrain_list_edges`.

## Rules for changes

Do not add tools that import `masterbrain.store` or touch the vault
filesystem - the HTTP API is the single enforcement point (PROCESS.md
rule 11; Phase 3b D1). Any new capability gets a spec and Clint's approval
first.
