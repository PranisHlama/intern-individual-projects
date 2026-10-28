import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from odoo.api import Environment

from ..registry import McpTool
from ..registry import McpToolRegistry


_TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*",
)


@dataclass(frozen=True)
class KnowledgeChunk:
    document: str
    section: str | None
    content: str


class KnowledgeIndex:

    def __init__(self) -> None:
        self._chunks: list[KnowledgeChunk] = []
        self._fingerprint: tuple[tuple[str, int, int], ...] = ()

    @staticmethod
    def _root() -> Path:
        root = os.environ.get(
            "AI_KNOWLEDGE_ROOT",
            "/mnt/ai_chat_knowledge",
        )

        return Path(root).resolve()

    @classmethod
    def _markdown_root(cls) -> Path:
        root = cls._root()

        markdown_root = root / "markdown"

        if markdown_root.exists():
            return markdown_root

        return root

    @staticmethod
    def _tokenize(
        text: str,
    ) -> list[str]:
        return [
            token.lower()
            for token in _TOKEN_PATTERN.findall(
                text,
            )
        ]

    @staticmethod
    def _chunk_text(
        text: str,
        max_chars: int = 2200,
        overlap: int = 250,
    ) -> list[str]:

        normalized = text.strip()

        if not normalized:
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                normalized,
            )
            if paragraph.strip()
        ]

        if not paragraphs:
            return []

        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:

            if not current:
                current = paragraph
                continue

            candidate = (
                f"{current}\n\n{paragraph}"
            )

            if len(candidate) <= max_chars:
                current = candidate
                continue

            chunks.append(current)

            if overlap > 0 and len(current) > overlap:
                carry = current[-overlap:]
            else:
                carry = ""

            current = (
                f"{carry}\n\n{paragraph}"
                if carry
                else paragraph
            )

        if current:
            chunks.append(current)

        return chunks

    @staticmethod
    def _split_sections(
        markdown: str,
    ) -> list[tuple[str | None, str]]:

        lines = markdown.splitlines()

        sections: list[
            tuple[str | None, list[str]]
        ] = []

        current_section: str | None = None
        current_lines: list[str] = []

        for line in lines:

            heading = re.match(
                r"^#{1,6}\s+(.+?)\s*$",
                line,
            )

            if heading:

                if current_lines:
                    sections.append(
                        (
                            current_section,
                            current_lines,
                        ),
                    )

                current_section = (
                    heading.group(1).strip()
                )

                current_lines = [
                    line,
                ]

                continue

            current_lines.append(line)

        if current_lines:
            sections.append(
                (
                    current_section,
                    current_lines,
                ),
            )

        return [
            (
                section,
                "\n".join(lines),
            )
            for section, lines in sections
        ]

    @classmethod
    def _load_chunks(
        cls,
    ) -> list[KnowledgeChunk]:

        markdown_root = cls._markdown_root()

        if not markdown_root.exists():
            return []

        chunks: list[KnowledgeChunk] = []

        for path in sorted(
            markdown_root.rglob("*.md"),
        ):

            if not path.is_file():
                continue

            try:
                markdown = path.read_text(
                    encoding="utf-8",
                )
            except (
                OSError,
                UnicodeDecodeError,
            ):
                continue

            try:
                relative_path = path.relative_to(
                    markdown_root,
                )
            except ValueError:
                relative_path = path.name

            document_name = str(
                relative_path,
            )

            for section, content in (
                cls._split_sections(
                    markdown,
                )
            ):

                for chunk in cls._chunk_text(
                    content,
                ):
                    chunks.append(
                        KnowledgeChunk(
                            document=document_name,
                            section=section,
                            content=chunk,
                        ),
                    )

        return chunks

    @classmethod
    def _build_fingerprint(
        cls,
    ) -> tuple[tuple[str, int, int], ...]:

        markdown_root = cls._markdown_root()

        if not markdown_root.exists():
            return ()

        files: list[
            tuple[str, int, int]
        ] = []

        for path in sorted(
            markdown_root.rglob("*.md"),
        ):

            if not path.is_file():
                continue

            try:
                stat = path.stat()
            except OSError:
                continue

            files.append(
                (
                    str(
                        path.relative_to(
                            markdown_root,
                        ),
                    ),

                    stat.st_mtime_ns,

                    stat.st_size,
                ),
            )

        return tuple(files)

    def refresh_if_changed(
        self,
    ) -> None:

        fingerprint = (
            self._build_fingerprint()
        )

        if (
            fingerprint ==
            self._fingerprint
        ):
            return

        self._chunks = (
            self._load_chunks()
        )

        self._fingerprint = fingerprint

    @staticmethod
    def _score(
        query_tokens: list[str],
        chunk_tokens: list[str],
        document_frequency: dict[str, int],
        total_chunks: int,
    ) -> float:

        if not query_tokens:
            return 0.0

        if not chunk_tokens:
            return 0.0

        token_counts: dict[str, int] = {}

        for token in chunk_tokens:
            token_counts[token] = (
                token_counts.get(
                    token,
                    0,
                )
                + 1
            )

        unique_query_tokens = set(
            query_tokens,
        )

        score = 0.0

        for token in unique_query_tokens:

            frequency = token_counts.get(
                token,
                0,
            )

            if frequency == 0:
                continue

            document_count = (
                document_frequency.get(
                    token,
                    0,
                )
            )

            idf = math.log(
                (
                    total_chunks + 1
                )
                /
                (
                    document_count + 1
                )
            ) + 1.0

            score += (
                frequency
                * idf
            )

        return score

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:

        self.refresh_if_changed()

        query_tokens = self._tokenize(
            query,
        )

        if not query_tokens:
            return []

        if not self._chunks:
            return []

        document_frequency: dict[
            str,
            int,
        ] = {}

        for chunk in self._chunks:

            unique_tokens = set(
                self._tokenize(
                    chunk.content,
                ),
            )

            for token in unique_tokens:
                document_frequency[token] = (
                    document_frequency.get(
                        token,
                        0,
                    )
                    + 1
                )

        scored: list[
            tuple[float, KnowledgeChunk]
        ] = []

        for chunk in self._chunks:

            chunk_tokens = self._tokenize(
                chunk.content,
            )

            score = self._score(
                query_tokens,
                chunk_tokens,
                document_frequency,
                len(self._chunks),
            )

            if score <= 0:
                continue

            scored.append(
                (
                    score,
                    chunk,
                ),
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results: list[
            dict[str, Any]
        ] = []

        for score, chunk in scored[:limit]:

            results.append(
                {
                    "document":
                        chunk.document,

                    "section":
                        chunk.section,

                    "score":
                        round(
                            score,
                            4,
                        ),

                    "content":
                        chunk.content,
                },
            )

        return results


knowledge_index = KnowledgeIndex()


def search_knowledge(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:

    query = arguments.get(
        "query",
    )

    if not isinstance(
        query,
        str,
    ):
        raise ValueError(
            "query is required",
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "query cannot be empty",
        )

    raw_limit = arguments.get(
        "limit",
        5,
    )

    try:
        limit = int(
            raw_limit,
        )
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "limit must be an integer",
        ) from error

    limit = max(
        1,
        min(
            limit,
            10,
        ),
    )

    results = knowledge_index.search(
        query,
        limit,
    )

    return {
        "query": query,

        "result_count":
            len(results),

        "results":
            results,
    }


def register_knowledge_tools(
    registry: McpToolRegistry,
) -> None:

    registry.register(
        McpTool(
            name="search_knowledge",

            description=(
                "Search the available company "
                "knowledge documents and return "
                "the most relevant Markdown chunks "
                "for the user's question."
            ),

            input_schema={
                "type": "object",

                "properties": {
                    "query": {
                        "type": "string",

                        "description": (
                            "Natural-language question "
                            "or search query."
                        ),
                    },

                    "limit": {
                        "type": "integer",

                        "minimum": 1,

                        "maximum": 10,

                        "default": 5,

                        "description": (
                            "Maximum number of relevant "
                            "knowledge chunks to return."
                        ),
                    },
                },

                "required": [
                    "query",
                ],

                "additionalProperties": False,
            },

            handler=search_knowledge,
        ),
    )
