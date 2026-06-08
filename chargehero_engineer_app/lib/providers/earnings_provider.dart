import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';

class EarningsProvider with ChangeNotifier {
  EarningsProvider();

  // Earnings data
  double totalEarnings = 0.0;
  double monthlyEarnings = 0.0;
  double pendingEarnings = 0.0;
  int completedJobs = 0;
  double averageRating = 0.0;

  // Job history
  List<Map<String, dynamic>> jobHistory = [];

  // Statistics
  Map<String, dynamic> statistics = {};

  bool isLoading = false;
  String? error;

  /// Fetch engineer earnings overview
  Future<void> fetchEarnings(String engineerId) async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/engineers/$engineerId/earnings');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        totalEarnings = (data['total_earnings'] ?? 0.0).toDouble();
        monthlyEarnings = (data['monthly_earnings'] ?? 0.0).toDouble();
        pendingEarnings = (data['pending_earnings'] ?? 0.0).toDouble();
        completedJobs = data['completed_jobs'] ?? 0;
        averageRating = (data['average_rating'] ?? 0.0).toDouble();
      } else {
        error = 'Failed to fetch earnings';
      }
    } catch (e) {
      error = e.toString();
    }

    isLoading = false;
    notifyListeners();
  }

  /// Fetch job history with earnings details
  Future<void> fetchJobHistory(String engineerId) async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final url = Uri.parse('${Config.apiBaseUrl}/engineers/$engineerId/service-reports');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        jobHistory = data.cast<Map<String, dynamic>>();
      } else {
        error = 'Failed to fetch job history';
      }
    } catch (e) {
      error = e.toString();
    }

    isLoading = false;
    notifyListeners();
  }

  /// Fetch earnings statistics
  Future<void> fetchStatistics(String engineerId) async {
    try {
      final url = Uri.parse('${Config.apiBaseUrl}/engineers/$engineerId/statistics');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        statistics = jsonDecode(response.body);
      }
    } catch (e) {
      error = e.toString();
    }

    notifyListeners();
  }

  /// Calculate earnings for a period
  double calculatePeriodEarnings(List<Map<String, dynamic>> reports, String period) {
    // period: 'daily', 'weekly', 'monthly', 'yearly'
    double total = 0.0;

    for (var report in reports) {
      final createdAt = DateTime.parse(report['created_at'] ?? DateTime.now().toIso8601String());
      final now = DateTime.now();

      bool include = false;
      if (period == 'daily') {
        include = createdAt.day == now.day &&
                 createdAt.month == now.month &&
                 createdAt.year == now.year;
      } else if (period == 'weekly') {
        final dayDiff = now.difference(createdAt).inDays;
        include = dayDiff >= 0 && dayDiff < 7;
      } else if (period == 'monthly') {
        include = createdAt.month == now.month && createdAt.year == now.year;
      } else if (period == 'yearly') {
        include = createdAt.year == now.year;
      }

      if (include) {
        total += (report['amount'] ?? 0.0).toDouble();
      }
    }

    return total;
  }

  /// Get job details for a specific report
  Map<String, dynamic>? getJobDetails(String reportId) {
    for (var job in jobHistory) {
      if (job['id'] == reportId) {
        return job;
      }
    }
    return null;
  }

  /// Calculate average rating from completed jobs
  double calculateAverageRating() {
    if (jobHistory.isEmpty) return 0.0;

    final ratedJobs = jobHistory.where((j) => j['rating_by_customer'] != null).toList();
    if (ratedJobs.isEmpty) return 0.0;

    final sum = ratedJobs.fold<double>(
      0.0,
      (prev, job) => prev + ((job['rating_by_customer'] ?? 0).toDouble())
    );

    return sum / ratedJobs.length;
  }

  /// Clear all data
  void clear() {
    totalEarnings = 0.0;
    monthlyEarnings = 0.0;
    pendingEarnings = 0.0;
    completedJobs = 0;
    averageRating = 0.0;
    jobHistory = [];
    statistics = {};
    error = null;
    notifyListeners();
  }
}
