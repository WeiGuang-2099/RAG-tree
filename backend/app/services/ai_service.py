"""ZhipuAI client wrapper service."""

import hashlib

from app.config import get_settings
from typing import AsyncGenerator


class AiService:
    """Wrapper for ZhipuAI API interactions."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._embedding_cache: dict[str, list[float]] = {}

    def _get_client(self):
        if self._client is None:
            try:
                from zhipuai import ZhipuAI
                self._client = ZhipuAI(api_key=self.settings.zhipuai_api_key)
            except ImportError:
                raise RuntimeError("zhipuai package is not installed.")
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text using Embedding-3."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        if self.settings.embedding_cache_enabled and text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]

        client = self._get_client()
        response = client.embeddings.create(
            model="embedding-3",
            input=text,
        )
        embedding = response.data[0].embedding

        if self.settings.embedding_cache_enabled:
            self._embedding_cache[text_hash] = embedding

        return embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts using Embedding-3."""
        if not self.settings.embedding_cache_enabled:
            client = self._get_client()
            response = client.embeddings.create(
                model="embedding-3",
                input=texts,
            )
            return [item.embedding for item in response.data]

        # Check cache for each text
        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            if text_hash in self._embedding_cache:
                results[i] = self._embedding_cache[text_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Fetch embeddings for uncached texts
        if uncached_texts:
            client = self._get_client()
            response = client.embeddings.create(
                model="embedding-3",
                input=uncached_texts,
            )

            for idx, embedding in zip(uncached_indices, response.data):
                text_hash = hashlib.sha256(texts[idx].encode()).hexdigest()
                self._embedding_cache[text_hash] = embedding.embedding
                results[idx] = embedding.embedding

        return results  # type: ignore[return-value]

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def find_similar_nodes(
        self,
        query: str,
        nodes: list[dict],
        top_k: int = 10,
    ) -> list[dict]:
        """Find the most similar nodes to a query using Embedding-3.

        Args:
            query: The search query text.
            nodes: List of node dicts, each must have a 'name' key and
                   optionally 'source_code', 'type', 'file_path'.
            top_k: Number of top results to return.

        Returns:
            List of node dicts sorted by similarity, with 'similarity' score added.
        """
        if not nodes:
            return []

        texts = []
        for node in nodes:
            parts = [node.get("name", "")]
            if node.get("type"):
                parts.append(f"({node['type']})")
            if node.get("file_path"):
                parts.append(f"in {node['file_path']}")
            if node.get("source_code"):
                code = node["source_code"]
                if len(code) > 500:
                    code = code[:500]
                parts.append(code)
            texts.append(" ".join(parts))

        query_vec = self.embed_text(query)
        node_vecs = self.embed_texts(texts)

        scored = []
        for i, (node, vec) in enumerate(zip(nodes, node_vecs)):
            score = self.cosine_similarity(query_vec, vec)
            scored.append({**node, "similarity": score})

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _serialize_graph_context(
        subgraph_nodes: list[dict],
        subgraph_edges: list[dict],
    ) -> str:
        """Convert a NetworkX subgraph into structured text for LLM consumption.

        Produces an indented tree format showing node hierarchy and relationships.
        Output is truncated to ~2000 characters.
        """
        if not subgraph_nodes:
            return ""

        # Build adjacency: node_id -> list of (target_name, edge_type)
        adj_out: dict[str, list[tuple[str, str]]] = {}
        for edge in subgraph_edges:
            src = edge.get("source", "")
            tgt_name = edge.get("target", "")
            edge_type = edge.get("type", "relates_to")
            adj_out.setdefault(src, []).append((tgt_name, edge_type))

        # Index nodes by id for name lookups
        node_by_id: dict[str, dict] = {n.get("id", ""): n for n in subgraph_nodes}

        lines: list[str] = []
        for node in subgraph_nodes:
            nid = node.get("id", "")
            name = node.get("name", nid)
            ntype = node.get("type", "Unknown")
            fpath = node.get("file_path", "")
            line_info = f" ({fpath})" if fpath else ""
            lines.append(f"{ntype}: {name}{line_info}")

            # Add outgoing relationships as indented children
            for tgt_id, edge_type in adj_out.get(nid, []):
                tgt_node = node_by_id.get(tgt_id, {})
                tgt_name = tgt_node.get("name", tgt_id)
                tgt_type = tgt_node.get("type", "")
                label = f"{tgt_type}: {tgt_name}" if tgt_type else tgt_name
                lines.append(f"  -{edge_type}-> {label}")

        result = "\n".join(lines)

        # Truncate to ~2000 characters, keeping complete lines
        if len(result) > 2000:
            result = result[:2000].rsplit("\n", 1)[0] + "\n..."

        return result

    async def chat(
        self,
        message: str,
        graph_context: str = "",
        node_context: str = "",
        history: list[dict] = [],
    ) -> str:
        """Send a chat message with code graph context."""
        client = self._get_client()

        system_prompt = (
            "You are a code analysis assistant. "
            "You help developers understand code structure, dependencies, "
            "and relationships in their codebase using graph-based analysis. "
            "Provide clear, concise, and technically accurate responses."
        )

        user_content = message
        if graph_context:
            user_content = f"Graph context: {graph_context}\n\n{user_content}"
        if node_context:
            user_content = f"{user_content}\n\nRelevant code:\n{node_context}"

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_content})

        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                timeout=self.settings.ai_timeout,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"AI service error: {str(e)}")

    async def analyze_architecture(
        self,
        nodes_summary: str,
        edges_summary: str,
    ) -> str:
        """Analyze project architecture based on graph data."""
        client = self._get_client()

        prompt = (
            "Analyze the following code architecture and provide a structured overview:\n\n"
            f"Nodes:\n{nodes_summary}\n\n"
            f"Edges:\n{edges_summary}\n\n"
            "Provide: 1) Architecture pattern identification, "
            "2) Module dependency analysis, "
            "3) Potential issues or suggestions."
        )

        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software architect.",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=self.settings.ai_timeout,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"AI service error: {str(e)}")

    async def analyze_architecture_stream(
        self,
        nodes_summary: str,
        edges_summary: str,
    ) -> AsyncGenerator[str, None]:
        """Stream architecture analysis using ZhipuAI."""
        client = self._get_client()

        prompt = (
            "Analyze the following code architecture and provide a structured overview:\n\n"
            f"Nodes:\n{nodes_summary}\n\n"
            f"Edges:\n{edges_summary}\n\n"
            "Provide: 1) Architecture pattern identification, "
            "2) Module dependency analysis, "
            "3) Potential issues or suggestions."
        )

        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software architect. Respond in a clear, structured format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                timeout=self.settings.ai_timeout,
            )
            for chunk in response:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    yield delta.content
        except Exception as e:
            raise RuntimeError(f"AI streaming error: {str(e)}")
