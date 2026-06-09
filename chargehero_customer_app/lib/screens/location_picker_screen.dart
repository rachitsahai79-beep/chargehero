import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';

/// Full-screen map for picking a charger location.
/// Tap the map to drop a pin, or use the current GPS location.
/// Returns the selected [LatLng] via Navigator.pop.
class LocationPickerScreen extends StatefulWidget {
  final LatLng? initial;
  const LocationPickerScreen({Key? key, this.initial}) : super(key: key);

  @override
  State<LocationPickerScreen> createState() => _LocationPickerScreenState();
}

class _LocationPickerScreenState extends State<LocationPickerScreen> {
  final MapController _mapController = MapController();
  // Default center: India (New Delhi) until a pin or GPS fix is set.
  LatLng _selected = const LatLng(28.6139, 77.2090);
  bool _hasPin = false;
  bool _locating = false;

  @override
  void initState() {
    super.initState();
    if (widget.initial != null) {
      _selected = widget.initial!;
      _hasPin = true;
    }
  }

  Future<void> _useMyLocation() async {
    setState(() => _locating = true);
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) {
        throw Exception('Location permission denied');
      }
      final pos = await Geolocator.getCurrentPosition();
      final here = LatLng(pos.latitude, pos.longitude);
      setState(() {
        _selected = here;
        _hasPin = true;
      });
      _mapController.move(here, 16);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not get location: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pick charger location'),
        actions: [
          TextButton(
            onPressed: _hasPin
                ? () => Navigator.of(context).pop(_selected)
                : null,
            child: Text(
              'DONE',
              style: TextStyle(
                color: _hasPin ? Colors.white : Colors.white54,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _selected,
              initialZoom: _hasPin ? 16 : 5,
              onTap: (tapPosition, point) {
                setState(() {
                  _selected = point;
                  _hasPin = true;
                });
              },
            ),
            children: [
              TileLayer(
                urlTemplate:
                    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.chargehero.customer',
              ),
              if (_hasPin)
                MarkerLayer(
                  markers: [
                    Marker(
                      point: _selected,
                      width: 44,
                      height: 44,
                      child: const Icon(
                        Icons.location_on,
                        color: Colors.red,
                        size: 44,
                      ),
                    ),
                  ],
                ),
            ],
          ),
          Positioned(
            top: 12,
            left: 12,
            right: 12,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  _hasPin
                      ? 'Selected: ${_selected.latitude.toStringAsFixed(5)}, ${_selected.longitude.toStringAsFixed(5)}'
                      : 'Tap the map to drop a pin, or use your location.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _locating ? null : _useMyLocation,
        icon: _locating
            ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
              )
            : const Icon(Icons.my_location),
        label: const Text('My location'),
      ),
    );
  }
}
