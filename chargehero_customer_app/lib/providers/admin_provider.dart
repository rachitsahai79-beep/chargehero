import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';
import 'charger_provider.dart';

/// Provider for admin-only data: all chargers, engineers, and dashboard stats.
/// Engineers and dashboard are kept as raw maps so the UI tolerates backend
/// schema changes without crashing.
class AdminProvider with ChangeNotifier {
  List<Charger> _allChargers = [];
  List<Map<String, dynamic>> _engineers = [];
  Map<String, dynamic>? _dashboard;
  bool _isLoading = false;
  String? _error;

  List<Charger> get allChargers => _allChargers;
  List<Map<String, dynamic>> get engineers => _engineers;
  Map<String, dynamic>? get dashboard => _dashboard;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchAll(String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    await Future.wait([
      _fetchChargers(token),
      _fetchEngineers(token),
      _fetchDashboard(token),
    ]);
    _isLoading = false;
    notifyListeners();
  }

  Future<void> _fetchChargers(String token) async {
    try {
      final res = await http.get(
        Uri.parse('${Config.apiBaseUrl}/admin/chargers'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List;
        _allChargers = data.map((e) => Charger.fromJson(e)).toList();
      } else {
        _error = 'Failed to load chargers (${res.statusCode})';
      }
    } catch (e) {
      _error = e.toString();
    }
  }

  Future<void> _fetchEngineers(String token) async {
    try {
      final res = await http.get(
        Uri.parse('${Config.apiBaseUrl}/admin/engineers'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List;
        _engineers = data.map((e) => e as Map<String, dynamic>).toList();
      }
    } catch (_) {
      // Non-fatal; leave engineers empty.
    }
  }

  Future<void> _fetchDashboard(String token) async {
    try {
      final res = await http.get(
        Uri.parse('${Config.apiBaseUrl}/admin/dashboard'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (res.statusCode == 200) {
        _dashboard = jsonDecode(res.body) as Map<String, dynamic>;
      }
    } catch (_) {
      // Non-fatal; leave dashboard null.
    }
  }
}
