from __future__ import annotations

import json
import os
import re
from typing import Optional

import httpx

from app.models import Document

_CALL_ID = 0


def _next_id() -> int:
    global _CALL_ID
    _CALL_ID += 1
    return _CALL_ID


class AffineAdapter:
    """Calls a running affine-mcp-server HTTP instance via JSON-RPC 2.0."""

    def __init__(self) -> None:
        self.mcp_url = os.environ["AFFINE_MCP_URL"]
        self.workspace_id = os.environ["AFFINE_WORKSPACE_ID"]
        self.api_token = os.getenv("AFFINE_API_TOKEN", "")

    # ------------------------------------------------------------------
    # BackendAdapter interface
    # ------------------------------------------------------------------

    def load_documents(self) -> list[Document]:
        return self._list_control_layer_docs()

    def load_drafts(self) -> list[Document]:
        return [d for d in self._list_control_layer_docs() if d.status.value == "draft"]

    def save_draft(self, doc: Document) -> None:
        # Create a new document in AFFiNE
        result = self._call("create_document", {
            "workspaceId": self.workspace_id,
            "title": doc.title,
        })
        affine_id = result.get("id") or result.get("docId") or doc.id

        metadata = {
            "document_type": doc.document_type.value,
            "status": doc.status.value,
            "version": doc.version,
            "owner": doc.owner,
            "updated_at": doc.updated_at,
            "source": doc.source,
            "tags": doc.tags,
            "supersedes": doc.supersedes,
        }

        self._call("append_blocks_to_document", {
            "workspaceId": self.workspace_id,
            "docId": affine_id,
            "blocks": [
                {
                    "type": "Code",
                    "language": "json",
                    "content": json.dumps(metadata, indent=2),
                },
                {
                    "type": "Paragraph",
                    "content": doc.content,
                },
            ],
        })

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        try:
            result = self._call("render_document_to_markdown", {
                "workspaceId": self.workspace_id,
                "docId": doc_id,
            })
            markdown = result.get("markdown") or result.get("content") or ""
            return self._parse_document(doc_id, "", markdown)
        except httpx.HTTPStatusError:
            return None
        except (KeyError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_control_layer_docs(self) -> list[Document]:
        result = self._call("list_workspace_documents", {
            "workspaceId": self.workspace_id,
        })
        raw_docs = result if isinstance(result, list) else result.get("docs", [])

        documents: list[Document] = []
        for raw in raw_docs:
            doc_id = raw.get("id") or raw.get("docId", "")
            title = raw.get("title", "")
            try:
                md_result = self._call("render_document_to_markdown", {
                    "workspaceId": self.workspace_id,
                    "docId": doc_id,
                })
                markdown = md_result.get("markdown") or md_result.get("content") or ""
                doc = self._parse_document(doc_id, title, markdown)
                if doc is not None:
                    documents.append(doc)
            except (httpx.HTTPStatusError, KeyError, ValueError):
                continue

        return documents

    def _parse_document(self, doc_id: str, title: str, markdown: str) -> Optional[Document]:
        """Extract control-layer metadata from the first JSON code block."""
        match = re.search(r"```json\s*\n([\s\S]*?)\n```", markdown)
        if not match:
            return None
        try:
            meta = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

        # Content is everything after the first code block
        content = markdown[match.end():].strip()

        return Document(
            id=doc_id,
            title=meta.get("title", title),
            document_type=meta["document_type"],
            status=meta["status"],
            version=meta["version"],
            owner=meta["owner"],
            updated_at=meta.get("updated_at", ""),
            source=meta.get("source", "affine"),
            tags=meta.get("tags", []),
            supersedes=meta.get("supersedes"),
            content=content,
        )

    def _call(self, tool_name: str, arguments: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": _next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        resp = httpx.post(self.mcp_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        body = resp.json()

        if "error" in body:
            raise ValueError(f"AFFiNE MCP error: {body['error']}")

        result = body.get("result", {})
        # MCP tool responses wrap content in a list of content blocks
        if isinstance(result, dict) and "content" in result:
            content_blocks = result["content"]
            if content_blocks and isinstance(content_blocks[0], dict):
                text = content_blocks[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"content": text}
        return result
