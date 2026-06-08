// chargehero_engineer_app/lib/screens/live_navigation_screen.dart
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:provider/provider.dart';
import '../providers/job_provider.dart';
import '../providers/location_provider.dart';

class LiveNavigationScreen extends StatefulWidget {
  const LiveNavigationScreen({Key? key}) : super(key: key);

  @override
  State<LiveNavigationScreen> createState() => _LiveNavigationScreenState();
}

class _LiveNavigationScreenState extends State<LiveNavigationScreen> {
  late GoogleMapController mapController;

  @override
  void initState() {
    super.initState();
    context.read<LocationProvider>().startLocationUpdates();
  }

  @override
  void dispose() {
    mapController.dispose();
    context.read<LocationProvider>().stopLocationUpdates();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Live Navigation'),
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Map
          Consumer2<LocationProvider, JobProvider>(
            builder: (context, locationProvider, jobProvider, child) {
              final job = jobProvider.selectedJob;
              final currentLocation = locationProvider.currentLocation;

              if (job == null || currentLocation == null) {
                return const Center(
                  child: CircularProgressIndicator(),
                );
              }

              return GoogleMap(
                onMapCreated: (controller) => mapController = controller,
                initialCameraPosition: CameraPosition(
                  target: LatLng(currentLocation.latitude!, currentLocation.longitude!),
                  zoom: 16,
                ),
                markers: {
                  // Current location marker
                  Marker(
                    markerId: const MarkerId('current'),
                    position: LatLng(currentLocation.latitude!, currentLocation.longitude!),
                    icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
                    infoWindow: const InfoWindow(title: 'Your Location'),
                  ),
                  // Job location marker
                  Marker(
                    markerId: const MarkerId('job'),
                    position: LatLng(job.latitude, job.longitude),
                    icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
                    infoWindow: InfoWindow(title: job.address),
                  ),
                },
                myLocationEnabled: true,
                myLocationButtonEnabled: true,
                polylines: {
                  Polyline(
                    polylineId: const PolylineId('route'),
                    points: [
                      LatLng(currentLocation.latitude!, currentLocation.longitude!),
                      LatLng(job.latitude, job.longitude),
                    ],
                    color: Colors.blue,
                    width: 3,
                  ),
                },
              );
            },
          ),

          // Bottom info panel
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Consumer2<LocationProvider, JobProvider>(
              builder: (context, locationProvider, jobProvider, child) {
                final job = jobProvider.selectedJob;
                final currentLocation = locationProvider.currentLocation;

                if (job == null || currentLocation == null) {
                  return const SizedBox.shrink();
                }

                // Calculate distance and ETA
                final distance = locationProvider.calculateDistance(
                  currentLocation.latitude!,
                  currentLocation.longitude!,
                  job.latitude,
                  job.longitude,
                );

                final eta = (distance / 40 * 60).toStringAsFixed(0); // ~40 km/h

                return Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Destination',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: Colors.grey,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        job.address,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildNavInfo(
                            'Distance',
                            '${distance.toStringAsFixed(1)} km',
                            Icons.location_on,
                          ),
                          _buildNavInfo(
                            'ETA',
                            '$eta min',
                            Icons.schedule,
                          ),
                          _buildNavInfo(
                            'Type',
                            job.getTicketTypeLabel(),
                            Icons.assignment,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            // Mark as arrived
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('You have arrived at the destination!'),
                              ),
                            );
                          },
                          icon: const Icon(Icons.check_circle),
                          label: const Text('Arrived at Location'),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavInfo(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: Colors.blue, size: 24),
        const SizedBox(height: 8),
        Text(
          label,
          style: const TextStyle(fontSize: 10, color: Colors.grey),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        ),
      ],
    );
  }
}
