// chargehero_engineer_app/lib/providers/job_provider.dart
import 'package:flutter/material.dart';

class Job {
  final String id;
  final String chargeId;
  final String chargerBrand;
  final String chargerModel;
  final String ticketType;
  final String priority;
  final String description;
  final String address;
  final double latitude;
  final double longitude;
  final int slaMinutes;
  final DateTime createdAt;

  Job({
    required this.id,
    required this.chargeId,
    required this.chargerBrand,
    required this.chargerModel,
    required this.ticketType,
    required this.priority,
    required this.description,
    required this.address,
    required this.latitude,
    required this.longitude,
    required this.slaMinutes,
    required this.createdAt,
  });

  Color getPriorityColor() {
    switch (priority) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.yellow;
      case 'low':
        return Colors.green;
      default:
        return Colors.blue;
    }
  }

  String getTicketTypeLabel() {
    switch (ticketType) {
      case 'preventive_maintenance':
        return 'Preventive Maintenance';
      case 'commission':
        return 'Commission';
      case 'issue':
        return 'Issue/Fault';
      default:
        return 'Service';
    }
  }
}

class JobProvider extends ChangeNotifier {
  List<Job> openJobs = [];
  List<Job> myJobs = [];
  Job? selectedJob;
  bool isLoading = false;
  String? error;

  Future<void> fetchOpenJobs() async {
    isLoading = true;
    notifyListeners();

    try {
      // TODO: Call API /api/v1/jobs/jobs/open
      // For now, populate with mock data
      openJobs = [
        Job(
          id: 'ticket-1',
          chargeId: 'charger-1',
          chargerBrand: 'ABB',
          chargerModel: '22kW',
          ticketType: 'preventive_maintenance',
          priority: 'high',
          description: 'Routine maintenance and inspection',
          address: '123 Main St, New Delhi',
          latitude: 28.7041,
          longitude: 77.1025,
          slaMinutes: 120,
          createdAt: DateTime.now(),
        ),
        Job(
          id: 'ticket-2',
          chargeId: 'charger-2',
          chargerBrand: 'Delta',
          chargerModel: '7.4kW',
          ticketType: 'issue',
          priority: 'critical',
          description: 'Display not working, needs diagnostics',
          address: '456 Park Ave, Gurgaon',
          latitude: 28.4595,
          longitude: 77.0266,
          slaMinutes: 60,
          createdAt: DateTime.now().subtract(Duration(hours: 1)),
        ),
      ];
      error = null;
    } catch (e) {
      error = 'Failed to fetch open jobs: $e';
    }

    isLoading = false;
    notifyListeners();
  }

  Future<void> fetchMyJobs() async {
    isLoading = true;
    notifyListeners();

    try {
      // TODO: Call API /api/v1/jobs/engineers/{id}/assignments
      myJobs = [];
      error = null;
    } catch (e) {
      error = 'Failed to fetch my jobs: $e';
    }

    isLoading = false;
    notifyListeners();
  }

  void selectJob(Job job) {
    selectedJob = job;
    notifyListeners();
  }

  Future<bool> acceptJob(String jobId) async {
    try {
      // TODO: Call API /api/v1/jobs/assignments/{id}/accept
      selectedJob = null;
      notifyListeners();
      return true;
    } catch (e) {
      error = 'Failed to accept job: $e';
      notifyListeners();
      return false;
    }
  }

  Future<bool> rejectJob(String jobId) async {
    try {
      // TODO: Call API /api/v1/jobs/assignments/{id}/reject
      return true;
    } catch (e) {
      error = 'Failed to reject job: $e';
      notifyListeners();
      return false;
    }
  }
}
