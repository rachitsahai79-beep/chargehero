"""Tests for copilot service."""

import pytest
from unittest.mock import MagicMock, patch
from domains.copilot.copilot_service import CopilotService


@pytest.fixture
def mock_db():
    """Mock database client."""
    return MagicMock()


@pytest.fixture
def copilot_service(mock_db):
    """Create CopilotService."""
    with patch('domains.copilot.copilot_service.anthropic.Anthropic'):
        return CopilotService(mock_db, 'test-api-key')


class TestCopilotQuery:
    """Test copilot query processing."""

    @patch('domains.copilot.copilot_service.CopilotService._generate_response')
    @patch('domains.copilot.copilot_service.CopilotService._search_knowledge_base')
    def test_query_copilot_success(self, mock_search, mock_generate, copilot_service, mock_db):
        """Successfully process a copilot query."""
        # Setup mocks
        mock_search.return_value = [
            {'id': 'kb-1', 'title': 'Voltage Issue', 'content': 'Check cables...', 'category': 'troubleshooting'}
        ]

        mock_generate.return_value = {
            'text': 'Try checking the voltage regulator...',
            'confidence': 0.95,
            'credits': 10
        }

        # Mock database insert
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'query-1',
            'engineer_id': 'engineer-1',
            'query': 'Why is voltage low?'
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'query': 'Why is voltage low?',
            'query_type': 'troubleshooting',
            'charger_brand': 'ABB'
        }

        result = copilot_service.query_copilot('engineer-1', data)

        assert result is not None
        assert result['id'] == 'query-1'
        assert 'response' in result


class TestKnowledgeBase:
    """Test knowledge base operations."""

    def test_add_knowledge_item_success(self, copilot_service, mock_db):
        """Successfully add a knowledge base item."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'kb-1',
            'title': 'Voltage Troubleshooting',
            'content': 'Check the voltage regulator...'
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'title': 'Voltage Troubleshooting',
            'content': 'Check the voltage regulator...',
            'category': 'troubleshooting',
            'charger_brand': 'ABB'
        }

        result = copilot_service.add_knowledge_base_item(data)

        assert result is not None
        assert result['id'] == 'kb-1'

    def test_get_knowledge_base_items(self, copilot_service, mock_db):
        """Get knowledge base items."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'kb-1', 'title': 'Item 1', 'category': 'troubleshooting'},
            {'id': 'kb-2', 'title': 'Item 2', 'category': 'maintenance'}
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        result = copilot_service.get_knowledge_base_items()

        assert len(result) == 2
        assert result[0]['id'] == 'kb-1'


class TestQueryHistory:
    """Test query history operations."""

    def test_get_query_history(self, copilot_service, mock_db):
        """Get copilot query history for an engineer."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'query-1', 'engineer_id': 'engineer-1', 'query': 'Test 1'},
            {'id': 'query-2', 'engineer_id': 'engineer-1', 'query': 'Test 2'}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_response

        result = copilot_service.get_query_history('engineer-1', limit=50)

        assert len(result) == 2
        assert result[0]['engineer_id'] == 'engineer-1'

    def test_store_feedback_success(self, copilot_service, mock_db):
        """Store feedback on copilot response."""
        mock_response = MagicMock()
        mock_response.data = [{'id': 'query-1', 'is_helpful': True}]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = copilot_service.store_feedback('query-1', True, 'Very helpful')

        assert result is True


class TestStatistics:
    """Test statistics calculation."""

    def test_get_statistics(self, copilot_service, mock_db):
        """Calculate copilot usage statistics."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'query-1', 'is_helpful': True, 'confidence_score': 0.95},
            {'id': 'query-2', 'is_helpful': True, 'confidence_score': 0.90},
            {'id': 'query-3', 'is_helpful': False, 'confidence_score': 0.70}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = copilot_service.get_statistics('engineer-1')

        assert result['total_queries'] == 3
        assert result['helpful_responses'] == 2
        assert result['unhelpful_responses'] == 1
        assert result['helpful_ratio'] == 0.67


class TestSearchAndContext:
    """Test knowledge base search and context building."""

    def test_search_knowledge_base(self, copilot_service, mock_db):
        """Search knowledge base for relevant items."""
        # Mock get_knowledge_base_items
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'kb-1',
                'title': 'Voltage Regulator Issue',
                'content': 'Voltage regulator troubleshooting steps',
                'charger_brand': 'ABB'
            },
            {
                'id': 'kb-2',
                'title': 'Cable Connection',
                'content': 'How to properly connect cables',
                'charger_brand': 'ABB'
            }
        ]
        mock_db.table.return_value.select.return_value.execute.return_value = mock_response

        result = copilot_service._search_knowledge_base('voltage issue', 'ABB')

        assert len(result) <= 3

    def test_build_context(self, copilot_service):
        """Build context from knowledge base items."""
        items = [
            {
                'id': 'kb-1',
                'title': 'Voltage Troubleshooting',
                'content': 'Check the voltage regulator',
                'category': 'troubleshooting',
                'charger_brand': 'ABB'
            }
        ]

        context = copilot_service._build_context(items)

        assert 'Voltage Troubleshooting' in context
        assert 'ABB' in context
        assert len(context) > 0

    def test_build_context_empty(self, copilot_service):
        """Build context with no items."""
        context = copilot_service._build_context([])
        assert 'No relevant' in context
