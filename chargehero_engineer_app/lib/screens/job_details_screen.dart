// chargehero_engineer_app/lib/screens/job_details_screen.dart
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:provider/provider.dart';
import '../providers/job_provider.dart';
import '../providers/location_provider.dart';

class JobDetailsScreen extends StatefulWidget {
  const JobDetailsScreen({Key? key}) : super(key: key);

  @override
  State<JobDetailsScreen> createState() => _JobDetailsScreenState();
}

class _JobDetailsScreenState extends State<JobDetailsScreen> {
  late GoogleMapController mapController;

  @override
  void initState() {
    super.initState();
    // Start location streaming when viewing job
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<LocationProvider>().startLocationUpdates();
    });
  }

  @override
  void dispose() {
    mapController.dispose();
    context.read<LocationProvider>().stopLocationUpdates();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<JobProvider>(
      builder: (context, jobProvider, child) {
        final job = jobProvider.selectedJob;

        if (job == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Job Details')),
            body: const Center(child: Text('No job selected')),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: const Text('Job Details'),
            elevation: 0,
          ),
          body: SingleChildScrollView(
            child: Column(
              children: [
                // Map
                SizedBox(
                  height: 250,
                  child: GoogleMap(
                    onMapCreated: (controller) => mapController = controller,
                    initialCameraPosition: CameraPosition(
                      target: LatLng(job.latitude, job.longitude),
                      zoom: 15,
                    ),
                    markers: {
                      Marker(
                        markerId: const MarkerId('job'),
                        position: LatLng(job.latitude, job.longitude),
                        infoWindow: InfoWindow(title: job.address),
                      ),
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Charger Info
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${job.chargerBrand} ${job.chargerModel}',
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                              const SizedBox(height: 8),
                              Text(
                                job.address,
                                style: Theme.of(context).textTheme.bodyMedium,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Job Details
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildDetailChip(
                            'Type',
                            job.getTicketTypeLabel(),
                            Icons.assignment,
                          ),
                          _buildDetailChip(
                            'Priority',
                            job.priority.toUpperCase(),
                            Icons.priority_high,
                            color: job.getPriorityColor(),
                          ),
                          _buildDetailChip(
                            'SLA',
                            '${job.slaMinutes}m',
                            Icons.schedule,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Description
                      Text(
                        'Description',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        job.description,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 24),

                      // Action Buttons
                      SizedBox(
                        width: double.infinity,
                        child: Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () {
                                  Navigator.pushNamed(context, '/live-navigation');
                                },
                                icon: const Icon(Icons.navigation),
                                label: const Text('Navigate'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () async {
                                  final success = await jobProvider.acceptJob(job.id);
                                  if (success && mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text('Job accepted!')),
                                    );
                                    Navigator.pop(context);
                                  }
                                },
                                icon: const Icon(Icons.check),
                                label: const Text('Accept'),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final confirmed = await showDialog<bool>(
                              context: context,
                              builder: (context) => AlertDialog(
                                title: const Text('Reject Job?'),
                                content: const Text(
                                  'Are you sure you want to reject this job?',
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(context, false),
                                    child: const Text('Cancel'),
                                  ),
                                  TextButton(
                                    onPressed: () => Navigator.pop(context, true),
                                    child: const Text('Reject'),
                                  ),
                                ],
                              ),
                            );

                            if (confirmed == true) {
                              await jobProvider.rejectJob(job.id);
                              if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Job rejected')),
                                );
                                Navigator.pop(context);
                              }
                            }
                          },
                          icon: const Icon(Icons.close),
                          label: const Text('Reject'),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDetailChip(
    String label,
    String value,
    IconData icon, {
    Color? color,
  }) {
    return Chip(
      avatar: Icon(icon, size: 18, color: color),
      label: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 10, color: Colors.grey),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
