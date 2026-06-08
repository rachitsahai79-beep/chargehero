import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';

class ChecklistItem {
  final String id;
  final String description;
  final String itemType;
  final bool? passed;
  final String? responseValue;
  final String? notes;
  final List<String> mediaUrls;

  ChecklistItem({
    required this.id,
    required this.description,
    required this.itemType,
    this.passed,
    this.responseValue,
    this.notes,
    required this.mediaUrls,
  });

  factory ChecklistItem.fromJson(Map<String, dynamic> json) {
    return ChecklistItem(
      id: json['id'],
      description: json['task_description'] ?? '',
      itemType: json['item_type'] ?? 'text',
      passed: json['passed'],
      responseValue: json['response_value'],
      notes: json['notes'],
      mediaUrls: (json['media'] as List?)?.map((m) => m['media_url'] as String).toList() ?? [],
    );
  }
}

class ChecklistResponse {
  final String id;
  final String ticketId;
  final String status;
  final String engineerName;
  final List<ChecklistItem> items;
  final int totalItems;
  final int completedItems;
  final double completionPercentage;
  final DateTime submittedAt;

  ChecklistResponse({
    required this.id,
    required this.ticketId,
    required this.status,
    required this.engineerName,
    required this.items,
    required this.totalItems,
    required this.completedItems,
    required this.completionPercentage,
    required this.submittedAt,
  });

  factory ChecklistResponse.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List?)?.map((i) => ChecklistItem.fromJson(i)).toList() ?? [];
    return ChecklistResponse(
      id: json['id'],
      ticketId: json['ticket_id'],
      status: json['status'] ?? 'in_progress',
      engineerName: json['engineer_name'] ?? 'Unknown',
      items: items,
      totalItems: json['total_items'] ?? items.length,
      completedItems: json['completed_items'] ?? 0,
      completionPercentage: (json['completion_percentage'] as num?)?.toDouble() ?? 0.0,
      submittedAt: DateTime.parse(json['submitted_at'] ?? DateTime.now().toIso8601String()),
    );
  }
}

class ChecklistProvider with ChangeNotifier {
  List<ChecklistResponse> _pendingChecklists = [];
  ChecklistResponse? _currentChecklist;
  bool _isLoading = false;
  String? _error;

  List<ChecklistResponse> get pendingChecklists => _pendingChecklists;
  ChecklistResponse? get currentChecklist => _currentChecklist;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch pending checklists for customer
  Future<void> fetchPendingChecklists(String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/checklists/pending');
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        _pendingChecklists = data.map((item) => ChecklistResponse.fromJson(item)).toList();
      } else {
        _error = 'Failed to fetch checklists';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch specific checklist details
  Future<void> fetchChecklistDetails(String checklistId, String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/checklists/$checklistId');
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _currentChecklist = ChecklistResponse.fromJson(data);
      } else {
        _error = 'Failed to fetch checklist';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Approve checklist
  Future<bool> approveChecklist(String checklistId, String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/checklists/$checklistId/approve');
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        // Remove from pending list
        _pendingChecklists.removeWhere((c) => c.id == checklistId);
        return true;
      } else {
        _error = 'Failed to approve checklist';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Reject checklist with reason
  Future<bool> rejectChecklist(String checklistId, String reason, String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/checklists/$checklistId/reject');
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'rejection_reason': reason,
        }),
      );

      if (response.statusCode == 200) {
        // Remove from pending list
        _pendingChecklists.removeWhere((c) => c.id == checklistId);
        return true;
      } else {
        _error = 'Failed to reject checklist';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
