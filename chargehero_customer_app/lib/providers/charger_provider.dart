import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';

class Charger {
  final String id;
  final String serialNumber;
  final String model;
  final String brand;
  final String address;
  final double latitude;
  final double longitude;
  final String status;
  final DateTime createdAt;

  Charger({
    required this.id,
    required this.serialNumber,
    required this.model,
    required this.brand,
    required this.address,
    required this.latitude,
    required this.longitude,
    required this.status,
    required this.createdAt,
  });

  factory Charger.fromJson(Map<String, dynamic> json) {
    return Charger(
      id: json['id'],
      serialNumber: json['serial_number'] ?? '',
      model: json['model'] ?? '',
      brand: json['brand'] ?? '',
      address: json['address'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0.0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'active',
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class Ticket {
  final String id;
  final String chargerId;
  final String type;
  final String priority;
  final String description;
  final String status;
  final String? assignedEngineer;
  final int slaMinutes;
  final DateTime createdAt;

  Ticket({
    required this.id,
    required this.chargerId,
    required this.type,
    required this.priority,
    required this.description,
    required this.status,
    this.assignedEngineer,
    required this.slaMinutes,
    required this.createdAt,
  });

  factory Ticket.fromJson(Map<String, dynamic> json) {
    return Ticket(
      id: json['id'],
      chargerId: json['charger_id'],
      type: json['ticket_type'],
      priority: json['priority'],
      description: json['description'] ?? '',
      status: json['status'],
      assignedEngineer: json['assigned_engineer_id'],
      slaMinutes: json['sla_minutes'] ?? 240,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class ChargerProvider with ChangeNotifier {
  List<Charger> _chargers = [];
  List<Ticket> _tickets = [];
  bool _isLoading = false;
  String? _error;

  List<Charger> get chargers => _chargers;
  List<Ticket> get tickets => _tickets;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch customer's chargers
  Future<void> fetchChargers(String token, String customerId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url =
          Uri.parse('${Config.apiBaseUrl}/jobs/customers/$customerId/chargers');
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        _chargers = data.map((item) => Charger.fromJson(item)).toList();
      } else {
        _error = 'Failed to fetch chargers';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch customer's tickets from the backend (persistent list).
  Future<void> fetchTickets(String token, String customerId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url =
          Uri.parse('${Config.apiBaseUrl}/jobs/customers/$customerId/tickets');
      final response = await http.get(
        url,
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        _tickets = data.map((item) => Ticket.fromJson(item)).toList();
      } else {
        _error = 'Failed to fetch tickets';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Update an existing charger.
  Future<bool> updateCharger({
    required String token,
    required String customerId,
    required String chargerId,
    required String serialNumber,
    required String model,
    required String brand,
    required String address,
    required double latitude,
    required double longitude,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/jobs/chargers/$chargerId');
      final response = await http.put(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'serial_number': serialNumber,
          'model': model,
          'brand': brand,
          'address': address,
          'latitude': latitude,
          'longitude': longitude,
        }),
      );

      if (response.statusCode == 200) {
        await fetchChargers(token, customerId);
        return true;
      } else {
        final data = jsonDecode(response.body);
        _error = data['detail'] ?? 'Failed to update charger';
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

  /// Delete a charger.
  Future<bool> deleteCharger({
    required String token,
    required String customerId,
    required String chargerId,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/jobs/chargers/$chargerId');
      final response = await http.delete(
        url,
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200 || response.statusCode == 204) {
        _chargers.removeWhere((c) => c.id == chargerId);
        return true;
      } else {
        final data = jsonDecode(response.body);
        _error = data['detail'] ?? 'Failed to delete charger';
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

  /// Raise a new ticket
  Future<bool> raiseTicket({
    required String token,
    required String chargerId,
    required String type,
    required String priority,
    required String description,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url =
          Uri.parse('${Config.apiBaseUrl}/jobs/chargers/$chargerId/tickets');
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'charger_id': chargerId,
          'ticket_type': type,
          'priority': priority,
          'description': description,
        }),
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        // No list endpoint exists; add the created ticket to the local list.
        final data = jsonDecode(response.body);
        _tickets.insert(0, Ticket.fromJson(data));
        return true;
      } else {
        final data = jsonDecode(response.body);
        _error = data['detail'] ?? 'Failed to raise ticket';
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

  /// Register a new charger
  Future<bool> registerCharger({
    required String token,
    required String customerId,
    required String serialNumber,
    required String model,
    required String brand,
    required String address,
    required double latitude,
    required double longitude,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/jobs/chargers');
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'serial_number': serialNumber,
          'model': model,
          'brand': brand,
          'address': address,
          'latitude': latitude,
          'longitude': longitude,
        }),
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        await fetchChargers(token, customerId);
        return true;
      } else {
        final data = jsonDecode(response.body);
        _error = data['detail'] ?? 'Failed to register charger';
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
