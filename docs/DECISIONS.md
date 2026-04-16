# Decisions

## 2026-04-16 — Control layer separate from Affine
- Status: accepted
- Reason: keep governance independent from storage layer

## 2026-04-16 — Control layer owns governance
- Status: accepted
- Decision: Governance rules are NOT embedded in Affine or MCP servers
- Impact: Control layer is single enforcement point

## 2026-04-16 — No direct agent access to source systems
- Status: accepted
- Decision: Agents never query Affine/Drive directly
- Impact: All access goes through control layer

## 2026-04-16 — MVP over completeness
- Status: accepted
- Decision: Build smallest working loop first
- Impact: No scaling, no infra, no abstractions yet
