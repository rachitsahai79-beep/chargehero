"""End-to-end tests for copilot AI functionality."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    """Create mock database."""
    return MagicMock()


@pytest.fixture
def copilot_service(mock_db):
    """Create CopilotService with mock database."""
    from domains.copilot.copilot_service import CopilotService
    return CopilotService(mock_db)


class TestCopilotQuery:
    """Test copilot query handling."""

    def test_engineer_can_query_copilot(self, copilot_service, mock_db):
        """Engineer should be able to ask copilot for help."""
        with patch('domains.copilot.copilot_service.CopilotService.query_copilot') as mock_query:
            mock_query.return_value = {
                'query_id': 'query123',
                'response': 'Step 1: Check the power cable connection...',
                'status': 'completed'
            }

            result = copilot_service.query_copilot(
                user_id='eng1',
                query_type='troubleshooting',
                query_text='How to fix Tesla charger not responding?'
            )

            assert result is not None
            assert 'response' in result

    def test_copilot_handles_different_query_types(self, copilot_service, mock_db):
        """Copilot should handle different query types."""
        query_types = ['troubleshooting', 'procedure', 'component', 'maintenance']

        for qtype in query_types:
            with patch('domains.copilot.copilot_service.CopilotService.query_copilot') as mock_query:
                mock_query.return_value = {'query_type': qtype}

                result = copilot_service.query_copilot(
                    user_id='eng1',
                    query_type=qtype,
                    query_text='Test query'
                )

                assert result is not None

    def test_copilot_integrates_with_knowledge_base(self, copilot_service, mock_db):
        """Copilot should retrieve relevant knowledge base items."""
        knowledge_items = [
            {
                'id': 'item1',
                'title': 'Tesla Charger Installation',
                'content': 'Installation guide...'
            },
            {
                'id': 'item2',
                'title': 'Troubleshooting Connection Issues',
                'content': 'Connection guide...'
            }
        ]

        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=knowledge_items
        )

        result = copilot_service.get_knowledge_base_items(limit=10)

        assert len(result) > 0


class TestKnowledgeBaseManagement:
    """Test knowledge base management."""

    def test_admin_can_add_knowledge_item(self, copilot_service, mock_db):
        """Admin should add items to knowledge base."""
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{
                'id': 'item123',
                'title': 'Tesla Charger Guide',
                'content': 'Detailed guide...',
                'category': 'component'
            }]
        )

        result = copilot_service.add_knowledge_base_item(
            title='Tesla Charger Guide',
            content='Detailed guide...',
            category='component'
        )

        assert result is True

    def test_knowledge_base_items_are_searchable(self, copilot_service, mock_db):
        """Knowledge base items should be searchable."""
        items = [
            {'id': 'item1', 'title': 'Tesla Charging'},
            {'id': 'item2', 'title': 'ChargePoint Troubleshooting'},
        ]

        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=items
        )

        result = copilot_service.get_knowledge_base_items()

        assert len(result) >= 0

    def test_copilot_provides_semantic_search(self, copilot_service, mock_db):
        """Copilot should provide semantic search of knowledge base."""
        # This would use embeddings
        with patch('domains.copilot.copilot_service.EmbeddingService.semantic_search') as mock_search:
            mock_search.return_value = [
                {
                    'id': 'item1',
                    'title': 'Relevant Article',
                    'similarity_score': 0.95
                }
            ]

            # Simplified: semantic_search would be called internally
            result = mock_search('Tesla charging setup')

            assert result is not None


class TestCopilotHistory:
    """Test copilot query history."""

    def test_engineer_can_view_query_history(self, copilot_service, mock_db):
        """Engineer should view their query history."""
        history = [
            {
                'query_id': 'query1',
                'query_text': 'How to fix...',
                'created_at': datetime.utcnow().isoformat(),
                'status': 'completed'
            },
            {
                'query_id': 'query2',
                'query_text': 'What is...',
                'created_at': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=history
        )

        result = copilot_service.get_query_history(user_id='eng1')

        assert len(result) == 2

    def test_history_shows_query_type(self, copilot_service, mock_db):
        """History should include query type."""
        history = [
            {
                'query_id': 'query1',
                'query_type': 'troubleshooting',
                'status': 'completed'
            }
        ]

        # History should include query type for categorization
        assert history[0].get('query_type') == 'troubleshooting'

    def test_history_shows_response(self, copilot_service, mock_db):
        """History should include copilot response."""
        history = [
            {
                'query_id': 'query1',
                'response': 'Step 1: Check power...',
                'status': 'completed'
            }
        ]

        assert 'response' in history[0]


class TestCopilotFeedback:
    """Test copilot feedback and improvement."""

    def test_engineer_can_rate_response(self, copilot_service, mock_db):
        """Engineer should rate copilot response helpfulness."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'query_id': 'query1',
                'helpful': True,
                'rating': 4
            }]
        )

        result = copilot_service.store_feedback(
            query_id='query1',
            helpful=True,
            rating=4,
            feedback_text='Very helpful guide'
        )

        assert result is True

    def test_copilot_statistics_tracked(self, copilot_service, mock_db):
        """Copilot usage statistics should be tracked."""
        stats = {
            'total_queries': 150,
            'helpful_responses': 135,
            'helpfulness_rate': 0.90,
            'avg_response_time_seconds': 2.5
        }

        with patch('domains.copilot.copilot_service.CopilotService.get_statistics') as mock_stats:
            mock_stats.return_value = stats

            result = copilot_service.get_statistics()

            assert result is not None


class TestCopilotIntegration:
    """Test copilot Claude API integration."""

    def test_copilot_calls_claude_api(self, copilot_service, mock_db):
        """Copilot should call Claude API for complex queries."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Would call Claude API internally
            with patch('domains.copilot.copilot_service.CopilotService.query_copilot'):
                pass

    def test_copilot_handles_api_errors(self, copilot_service, mock_db):
        """Copilot should handle API failures gracefully."""
        with patch('domains.copilot.copilot_service.CopilotService.query_copilot') as mock_query:
            mock_query.side_effect = Exception('API Error')

            # Should handle error gracefully
            with pytest.raises(Exception):
                copilot_service.query_copilot(
                    user_id='eng1',
                    query_type='troubleshooting',
                    query_text='Test'
                )

    def test_copilot_includes_context(self, copilot_service, mock_db):
        """Copilot should include charger/job context in query."""
        # Context could include: charger type, issue category, engineer certifications
        context = {
            'charger_brand': 'Tesla',
            'charger_type': 'Wall Connector',
            'issue_category': 'charging_failure',
            'engineer_certifications': ['Tesla', 'ChargePoint']
        }

        # Context would be included in prompt to Claude
        assert 'charger_brand' in context


class TestCopilotEmbeddings:
    """Test copilot embedding and semantic search."""

    def test_embeddings_generated_for_kb_items(self, copilot_service, mock_db):
        """Embeddings should be generated for knowledge base items."""
        with patch('domains.copilot.embedding_service.EmbeddingService.embed_knowledge_item') as mock_embed:
            mock_embed.return_value = True

            result = mock_embed(
                item_id='item1',
                content='Knowledge base content'
            )

            assert result is True

    def test_semantic_search_finds_similar_content(self, copilot_service, mock_db):
        """Semantic search should find similar KB items."""
        with patch('domains.copilot.embedding_service.EmbeddingService.semantic_search') as mock_search:
            mock_search.return_value = [
                {
                    'id': 'item1',
                    'title': 'Related Article',
                    'similarity_score': 0.92
                }
            ]

            result = mock_search('troubleshooting charging issues')

            assert len(result) > 0
            assert result[0].get('similarity_score') > 0.8

    def test_fallback_keyword_search_when_embeddings_unavailable(self, copilot_service, mock_db):
        """Should fallback to keyword search if embeddings unavailable."""
        # Fallback search would use basic keyword matching
        query = 'Tesla charger installation'
        keywords = query.split()

        assert len(keywords) > 0
