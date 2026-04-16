# Architecture

## Components
- Claude (agent)
- MCP server(s)
- Control layer (this repo)
- Source systems (Affine, Google Drive)

## Principle
Control layer governs:
- document selection
- version usage
- allowed actions

## Minimal Control Flow (MVP)

1. User prompt
2. Control layer interprets intent
3. Control layer selects allowed documents
4. Control layer applies rules
5. Control layer returns filtered output

## Responsibilities

Control Layer:
- Document selection
- Version control
- Rule enforcement

MCP:
- Access layer only

Affine:
- Storage only
