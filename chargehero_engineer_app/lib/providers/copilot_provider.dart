import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';

class CopilotMessage {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final List<String>? sources;
  final double? confidenceScore;

  CopilotMessage({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.sources,
    this.confidenceScore,
  });
}

class CopilotProvider with ChangeNotifier {
  final List<CopilotMessage> messages = [];
  bool isLoading = false;
  String? error;
  String? selectedQueryType = 'troubleshooting';
  String? chargerBrand;
  String? chargerModel;

  final List<String> queryTypes = [
    'troubleshooting',
    'procedure',
    'component',
    'maintenance',
    'other'
  ];

  /// Send a query to the copilot
  Future<void> askCopilot(String query, String engineerId, String token) async {
    if (query.isEmpty) return;

    isLoading = true;
    error = null;
    notifyListeners();

    try {
      // Add user message to chat
      messages.add(CopilotMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: query,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      notifyListeners();

      // Send query to backend
      final url = Uri.parse('${Config.apiBaseUrl}/copilot/query');
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'query': query,
          'query_type': selectedQueryType,
          'charger_brand': chargerBrand,
          'charger_model': chargerModel,
        }),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);

        // Add copilot response to chat
        messages.add(CopilotMessage(
          id: data['id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
          content: data['response'] ?? 'No response received',
          isUser: false,
          timestamp: DateTime.now(),
          sources: List<String>.from(data['sources'] ?? []),
          confidenceScore: (data['confidence_score'] as num?)?.toDouble(),
        ));
      } else {
        error = 'Failed to get response from copilot';
      }
    } catch (e) {
      error = e.toString();
    }

    isLoading = false;
    notifyListeners();
  }

  /// Provide feedback on a copilot response
  Future<void> provideFeedback(
    String queryId,
    bool isHelpful,
    String? feedback,
    String token,
  ) async {
    try {
      final url = Uri.parse('${Config.apiBaseUrl}/copilot/feedback/$queryId');
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'is_helpful': isHelpful,
          'feedback': feedback,
        }),
      );

      if (response.statusCode == 200) {
        // Feedback recorded successfully
      } else {
        error = 'Failed to record feedback';
        notifyListeners();
      }
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }

  /// Fetch copilot query history
  Future<void> fetchHistory(String engineerId, String token) async {
    try {
      final url = Uri.parse('${Config.apiBaseUrl}/copilot/history');
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        // Load history into messages
        for (var item in data) {
          messages.add(CopilotMessage(
            id: item['id'],
            content: item['query'] ?? '',
            isUser: true,
            timestamp: DateTime.parse(item['created_at']),
          ));

          messages.add(CopilotMessage(
            id: '${item['id']}-response',
            content: item['response'] ?? '',
            isUser: false,
            timestamp: DateTime.parse(item['created_at']),
          ));
        }
        notifyListeners();
      }
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }

  /// Clear all messages
  void clearChat() {
    messages.clear();
    error = null;
    notifyListeners();
  }

  /// Set query type
  void setQueryType(String type) {
    selectedQueryType = type;
    notifyListeners();
  }

  /// Set charger brand
  void setChargerBrand(String? brand) {
    chargerBrand = brand;
    notifyListeners();
  }

  /// Set charger model
  void setChargerModel(String? model) {
    chargerModel = model;
    notifyListeners();
  }
}
