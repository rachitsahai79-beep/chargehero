// chargehero_engineer_app/lib/providers/location_provider.dart
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:math';

class LocationProvider extends ChangeNotifier {
  Position? currentLocation;
  bool isTracking = false;
  String? error;

  Future<void> startLocationUpdates() async {
    try {
      // Check permissions
      final permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        await Geolocator.requestPermission();
      }

      isTracking = true;
      notifyListeners();

      // Get initial location
      currentLocation = await Geolocator.getCurrentPosition();
      notifyListeners();

      // Listen to position updates (every 10 seconds)
      Geolocator.getPositionStream(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.best,
          distanceFilter: 10, // 10 meters
        ),
      ).listen((Position position) {
        currentLocation = position;
        notifyListeners();
      });

      error = null;
    } catch (e) {
      error = 'Location error: $e';
      isTracking = false;
      notifyListeners();
    }
  }

  void stopLocationUpdates() {
    isTracking = false;
    notifyListeners();
  }

  double calculateDistance(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    const R = 6371; // Earth's radius in km
    final dLat = _toRad(lat2 - lat1);
    final dLon = _toRad(lon2 - lon1);
    final a = sin(dLat / 2) * sin(dLat / 2) +
        cos(_toRad(lat1)) * cos(_toRad(lat2)) * sin(dLon / 2) * sin(dLon / 2);
    final c = 2 * atan2(sqrt(a), sqrt(1 - a));
    return R * c; // Distance in km
  }

  double _toRad(double deg) {
    return deg * (pi / 180);
  }
}
