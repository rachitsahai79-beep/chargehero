import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/copilot_provider.dart';
import '../providers/job_provider.dart';

class CopilotChatScreen extends StatefulWidget {
  final String engineerId;
  final String token;

  const CopilotChatScreen({
    Key? key,
    required this.engineerId,
    required this.token,
  }) : super(key: key);

  @override
  State<CopilotChatScreen> createState() => _CopilotChatScreenState();
}

class _CopilotChatScreenState extends State<CopilotChatScreen> {
  final TextEditingController _queryController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _showFilters = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<CopilotProvider>();
      if (provider.messages.isEmpty) {
        provider.fetchHistory(widget.engineerId, widget.token);
      }
    });
  }

  @override
  void dispose() {
    _queryController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ChargeHero Copilot'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () {
              setState(() => _showFilters = !_showFilters);
            },
          ),
        ],
      ),
      body: Consumer<CopilotProvider>(
        builder: (context, provider, child) {
          return Column(
            children: [
              if (_showFilters) _buildFiltersPanel(provider),
              Expanded(
                child: provider.messages.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(12),
                        itemCount: provider.messages.length,
                        itemBuilder: (context, index) {
                          final message = provider.messages[index];
                          return _buildMessageBubble(provider, message);
                        },
                      ),
              ),
              if (provider.error != null)
                Container(
                  color: Colors.red.shade50,
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(Icons.error, color: Colors.red.shade700),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          provider.error!,
                          style: TextStyle(color: Colors.red.shade700),
                        ),
                      ),
                      IconButton(
                        icon: Icon(Icons.close, color: Colors.red.shade700),
                        onPressed: () {
                          provider.error = null;
                          provider.notifyListeners();
                        },
                      ),
                    ],
                  ),
                ),
              _buildInputArea(provider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildFiltersPanel(CopilotProvider provider) {
    return Container(
      color: Colors.grey.shade100,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Query Filters',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          DropdownButton<String>(
            isExpanded: true,
            value: provider.selectedQueryType,
            items: provider.queryTypes
                .map((type) => DropdownMenuItem(
                      value: type,
                      child: Text(type),
                    ))
                .toList(),
            onChanged: (type) {
              if (type != null) {
                provider.setQueryType(type);
              }
            },
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: InputDecoration(
              labelText: 'Charger Brand (Optional)',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              isDense: true,
            ),
            onChanged: (value) {
              provider.setChargerBrand(value.isEmpty ? null : value);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: InputDecoration(
              labelText: 'Charger Model (Optional)',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              isDense: true,
            ),
            onChanged: (value) {
              provider.setChargerModel(value.isEmpty ? null : value);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.smart_toy,
            size: 64,
            color: Colors.grey.shade300,
          ),
          const SizedBox(height: 16),
          Text(
            'ChargeHero Copilot',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            'Ask me about troubleshooting, procedures,\ncomponents, or maintenance.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.grey.shade600,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(CopilotProvider provider, CopilotMessage message) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!message.isUser)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Icon(
                Icons.smart_toy,
                size: 24,
                color: Colors.blue.shade400,
              ),
            ),
          Flexible(
            child: Column(
              crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  decoration: BoxDecoration(
                    color: message.isUser ? Colors.blue.shade500 : Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    message.content,
                    style: TextStyle(
                      color: message.isUser ? Colors.white : Colors.black87,
                      fontSize: 14,
                    ),
                  ),
                ),
                if (!message.isUser && message.confidenceScore != null) ...[
                  const SizedBox(height: 6),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.check_circle,
                          size: 14,
                          color: _getConfidenceColor(message.confidenceScore!),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Confidence: ${(message.confidenceScore! * 100).toStringAsFixed(0)}%',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                if (!message.isUser && message.sources != null && message.sources!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Sources:',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade700,
                          ),
                        ),
                        ...message.sources!.map((source) => Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            '• $source',
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        )),
                      ],
                    ),
                  ),
                ],
                if (!message.isUser) ...[
                  const SizedBox(height: 8),
                  _buildFeedbackButtons(provider, message),
                ],
              ],
            ),
          ),
          if (message.isUser)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Icon(
                Icons.account_circle,
                size: 24,
                color: Colors.blue.shade500,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildFeedbackButtons(CopilotProvider provider, CopilotMessage message) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 32,
          height: 28,
          child: IconButton(
            padding: EdgeInsets.zero,
            icon: const Icon(Icons.thumb_up_outlined, size: 16),
            onPressed: () {
              provider.provideFeedback(message.id, true, null, widget.token);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Feedback recorded')),
              );
            },
          ),
        ),
        SizedBox(
          width: 32,
          height: 28,
          child: IconButton(
            padding: EdgeInsets.zero,
            icon: const Icon(Icons.thumb_down_outlined, size: 16),
            onPressed: () {
              _showFeedbackDialog(provider, message.id);
            },
          ),
        ),
      ],
    );
  }

  void _showFeedbackDialog(CopilotProvider provider, String messageId) {
    final feedbackController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Feedback'),
        content: TextField(
          controller: feedbackController,
          decoration: const InputDecoration(
            hintText: 'Tell us what could be improved...',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              provider.provideFeedback(
                messageId,
                false,
                feedbackController.text,
                widget.token,
              );
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Thank you for your feedback')),
              );
            },
            child: const Text('Send'),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea(CopilotProvider provider) {
    return Container(
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: Colors.grey.shade300)),
      ),
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _queryController,
              decoration: InputDecoration(
                hintText: 'Ask copilot...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide(color: Colors.grey.shade300),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              maxLines: null,
              enabled: !provider.isLoading,
            ),
          ),
          const SizedBox(width: 8),
          FloatingActionButton(
            mini: true,
            onPressed: provider.isLoading
                ? null
                : () async {
                    final query = _queryController.text.trim();
                    if (query.isNotEmpty) {
                      _queryController.clear();
                      await provider.askCopilot(query, widget.engineerId, widget.token);

                      // Auto-scroll to bottom
                      Future.delayed(const Duration(milliseconds: 300), () {
                        if (_scrollController.hasClients) {
                          _scrollController.animateTo(
                            _scrollController.position.maxScrollExtent,
                            duration: const Duration(milliseconds: 300),
                            curve: Curves.easeOut,
                          );
                        }
                      });
                    }
                  },
            child: provider.isLoading
                ? SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation(Colors.grey.shade600),
                    ),
                  )
                : const Icon(Icons.send),
          ),
        ],
      ),
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return Colors.green;
    if (confidence >= 0.7) return Colors.blue;
    if (confidence >= 0.5) return Colors.orange;
    return Colors.red;
  }
}
