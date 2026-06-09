import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:math' as math;
import '../config.dart';

class EngineerLocation {
  final double latitude;
  final double longitude;
  final DateTime timestamp;
  final double? speed;

  EngineerLocation({
    required this.latitude,
    required this.longitude,
    required this.timestamp,
    this.speed,
  });

  factory EngineerLocation.fromJson(Map<String, dynamic> json) {
    return EngineerLocation(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      timestamp: DateTime.parse(json['updated_at']),
      speed: (json['speed'] as num?)?.toDouble(),
    );
  }
}

class TicketDetail {
  final String id;
  final String chargerId;
  final String status;
  final String type;
  final String priority;
  final String description;
  final String? assignedEngineer;
  final String? engineerName;
  final EngineerLocation? engineerLocation;
  final int slaMinutes;
  final int elapsedMinutes;
  final double etaMinutes;
  final String chargerAddress;
  final DateTime createdAt;

  TicketDetail({
    required this.id,
    required this.chargerId,
    required this.status,
    required this.type,
    required this.priority,
    required this.description,
    this.assignedEngineer,
    this.engineerName,
    this.engineerLocation,
    required this.slaMinutes,
    required this.elapsedMinutes,
    required this.etaMinutes,
    required this.chargerAddress,
    required this.createdAt,
  });

  factory TicketDetail.fromJson(Map<String, dynamic> json) {
    return TicketDetail(
      id: json['id'],
      chargerId: json['charger_id'],
      status: json['status'],
      type: json['ticket_type'],
      priority: json['priority'],
      description: json['description'] ?? '',
      assignedEngineer: json['assigned_engineer_id'],
      engineerName: json['engineer_name'],
      engineerLocation: json['engineer_location'] != null
          ? EngineerLocation.fromJson(json['engineer_location'])
          : null,
      slaMinutes: json['sla_minutes'] ?? 240,
      elapsedMinutes: json['elapsed_minutes'] ?? 0,
      etaMinutes: (json['eta_minutes'] as num?)?.toDouble() ?? 0.0,
      chargerAddress: json['charger_address'] ?? '',
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  bool get isOverSLA => elapsedMinutes > slaMinutes;
  int get slaRemainingMinutes => slaMinutes - elapsedMinutes;
  double get slaPercentage => (elapsedMinutes / slaMinutes * 100).clamp(0, 100);
}

class TicketTrackingProvider with ChangeNotifier {
  TicketDetail? _ticketDetail;
  bool _isLoading = false;
  String? _error;
  DateTime? _lastUpdate;

  TicketDetail? get ticketDetail => _ticketDetail;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasEngineerLocation => _ticketDetail?.engineerLocation != null;

  /// Fetch ticket details with real-time tracking
  Future<void> fetchTicketDetail(String ticketId, String token) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/tickets/$ticketId');
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _ticketDetail = TicketDetail.fromJson(data);
        _lastUpdate = DateTime.now();
      } else {
        _error = 'Failed to fetch ticket details';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Subscribe to real-time ticket updates (WebSocket would be ideal)
  /// For now, polling as fallback
  Future<void> startTracking(String ticketId, String token) async {
    while (_ticketDetail != null &&
           _ticketDetail!.status != 'closed' &&
           _ticketDetail!.status != 'resolved') {
      await Future.delayed(const Duration(seconds: 10));
      await fetchTicketDetail(ticketId, token);
    }
  }

  /// Get engineer's current location
  EngineerLocation? getEngineerLocation() => _ticketDetail?.engineerLocation;

  /// Calculate distance between two points (Haversine formula)
  static double calculateDistance(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    const p = 0.017453292519943295; // Math.PI / 180
    final c = math.cos((lat2 - lat1) * p / 2);
    return 12742 *
        math.asin(math.sqrt(math.sin((lat2 - lat1) * p / 2) * math.sin((lat2 - lat1) * p / 2) +
            math.cos(lat1 * p) *
                math.cos(lat2 * p) *
                math.sin((lon2 - lon1) * p / 2) *
                math.sin((lon2 - lon1) * p / 2)));
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
