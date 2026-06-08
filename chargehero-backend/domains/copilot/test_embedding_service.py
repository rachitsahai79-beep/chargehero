"""Tests for embedding service."""

import pytest
from unittest.mock import MagicMock, patch
import json
from domains.copilot.embedding_service import EmbeddingService


@pytest.fixture
def mock_db():
    """Mock database client."""
    return MagicMock()


@pytest.fixture
def embedding_service(mock_db):
    """Create EmbeddingService."""
    with patch('domains.copilot.embedding_service.anthropic.Anthropic'):
        return EmbeddingService(mock_db, 'test-api-key')


class TestEmbeddingGeneration:
    """Test embedding generation."""

    def test_generate_embedding(self, embedding_service):
        """Generate embedding for text."""
        text = "How to troubleshoot voltage issues"
        embedding = embedding_service.generate_embedding(text)

        assert embedding is not None
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_knowledge_item_success(self, embedding_service, mock_db):
        """Successfully embed a knowledge base item."""
        mock_response = MagicMock()
        mock_response.data = [{'id': 'kb-1', 'embedding': '[]'}]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = embedding_service.embed_knowledge_item('kb-1', 'Test content')

        assert result is True

    def test_simple_embedding_deterministic(self, embedding_service):
        """Verify simple embedding is deterministic."""
        text = "Test content"
        embedding1 = embedding_service._simple_embedding(text)
        embedding2 = embedding_service._simple_embedding(text)

        assert embedding1 == embedding2


class TestSemanticSearch:
    """Test semantic search functionality."""

    def test_cosine_similarity(self, embedding_service):
        """Calculate cosine similarity between vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = embedding_service._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self, embedding_service):
        """Cosine similarity of orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = embedding_service._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

    def test_keyword_similarity(self, embedding_service):
        """Calculate keyword similarity."""
        query = "voltage issue"
        item = {
            'title': 'Troubleshooting Voltage Issues',
            'content': 'Check the voltage regulator and connections'
        }

        similarity = embedding_service._keyword_similarity(query, item)
        assert similarity > 0

    def test_semantic_search_with_fallback(self, embedding_service, mock_db):
        """Semantic search with keyword fallback."""
        # Mock knowledge base items
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'kb-1',
                'title': 'Voltage Troubleshooting',
                'content': 'Check the voltage regulator',
                'embedding': None,
                'charger_brand': None,
                'charger_model': None
            }
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        results = embedding_service.semantic_search('voltage issue', limit=5)

        assert len(results) > 0

    def test_keyword_search(self, embedding_service, mock_db):
        """Keyword-based search fallback."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'kb-1',
                'title': 'Voltage Issues',
                'content': 'How to diagnose voltage problems',
                'charger_brand': 'ABB',
                'charger_model': None
            }
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        results = embedding_service._keyword_search('voltage diagnostic', limit=5)

        assert len(results) > 0


class TestBulkEmbedding:
    """Test bulk embedding operations."""

    def test_bulk_embed_knowledge_base(self, embedding_service, mock_db):
        """Bulk embed all knowledge base items."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'kb-1', 'title': 'Item 1', 'content': 'Content 1', 'embedding': None},
            {'id': 'kb-2', 'title': 'Item 2', 'content': 'Content 2', 'embedding': '[]'}
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        with patch.object(embedding_service, 'embed_knowledge_item', return_value=True):
            result = embedding_service.bulk_embed_knowledge_base()

        assert 'processed' in result
        assert 'failed' in result

    def test_get_embedding_stats(self, embedding_service, mock_db):
        """Get embedding statistics."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'kb-1', 'embedding': '[]'},
            {'id': 'kb-2', 'embedding': None},
            {'id': 'kb-3', 'embedding': '[]'}
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        result = embedding_service.get_embedding_stats()

        assert result['total_items'] == 3
        assert result['embedded_items'] == 2
        assert result['unembedded_items'] == 1
        assert result['coverage_percentage'] == pytest.approx(66.7)


class TestSearchFiltering:
    """Test search filtering by charger type."""

    def test_semantic_search_with_brand_filter(self, embedding_service, mock_db):
        """Semantic search filtered by charger brand."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'kb-1',
                'title': 'ABB Issue',
                'content': 'ABB specific issue',
                'embedding': None,
                'charger_brand': 'ABB',
                'charger_model': None
            },
            {
                'id': 'kb-2',
                'title': 'Generic Issue',
                'content': 'Any charger issue',
                'embedding': None,
                'charger_brand': None,
                'charger_model': None
            }
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        results = embedding_service.semantic_search('issue', charger_brand='ABB', limit=5)

        assert len(results) > 0
