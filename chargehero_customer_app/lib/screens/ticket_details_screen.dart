import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/auth_provider.dart';
import '../providers/ticket_tracking_provider.dart';

class TicketDetailsScreen extends StatefulWidget {
  final String ticketId;

  const TicketDetailsScreen({
    Key? key,
    required this.ticketId,
  }) : super(key: key);

  @override
  State<TicketDetailsScreen> createState() => _TicketDetailsScreenState();
}

class _TicketDetailsScreenState extends State<TicketDetailsScreen> {
  late TicketTrackingProvider _trackingProvider;

  @override
  void initState() {
    super.initState();
    _trackingProvider = context.read<TicketTrackingProvider>();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = context.read<AuthProvider>();
      _trackingProvider.fetchTicketDetail(widget.ticketId, authProvider.token!);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Ticket #${widget.ticketId.substring(0, 8)}'),
        elevation: 0,
      ),
      body: Consumer<TicketTrackingProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.ticketDetail == null) {
            return const Center(child: CircularProgressIndicator());
          }

          final ticket = provider.ticketDetail;
          if (ticket == null) {
            return Center(
              child: Text(provider.error ?? 'Failed to load ticket'),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.fetchTicketDetail(
              widget.ticketId,
              context.read<AuthProvider>().token!,
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              physics: const AlwaysScrollableScrollPhysics(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Status Card
                  Card(
                    elevation: 2,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _getStatusColor(ticket.status).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Status',
                                style: Theme.of(context).textTheme.titleSmall,
                              ),
                              Chip(
                                label: Text(ticket.status.replaceAll('_', ' ')),
                                backgroundColor:
                                    _getStatusColor(ticket.status),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          LinearProgressIndicator(
                            value: (ticket.slaPercentage / 100).clamp(0, 1),
                            minHeight: 8,
                            backgroundColor:
                                Colors.grey.shade300,
                            valueColor: AlwaysStoppedAnimation(
                              ticket.isOverSLA ? Colors.red : Colors.green,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'SLA: ${ticket.slaRemainingMinutes}m remaining',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: ticket.isOverSLA
                                      ? Colors.red
                                      : Colors.green,
                                ),
                              ),
                              Text(
                                '${ticket.elapsedMinutes}m elapsed',
                                style: const TextStyle(fontSize: 12),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Engineer Info
                  if (ticket.assignedEngineer != null)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Assigned Engineer',
                              style:
                                  Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                CircleAvatar(
                                  child: Text(
                                    (ticket.engineerName ?? 'E')
                                        .substring(0, 1)
                                        .toUpperCase(),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        ticket.engineerName ?? 'Unknown',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      if (ticket.engineerLocation != null)
                                        Text(
                                          'ETA: ${ticket.etaMinutes.toStringAsFixed(0)}m',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                if (ticket.engineerLocation != null)
                                  ElevatedButton.icon(
                                    onPressed: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) =>
                                              LiveTrackingScreen(
                                                ticketId: widget.ticketId,
                                              ),
                                        ),
                                      );
                                    },
                                    icon: const Icon(Icons.location_on),
                                    label: const Text('Track'),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),

                  const SizedBox(height: 20),

                  // Ticket Details
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Ticket Details',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 12),
                          _buildDetailRow('Type', ticket.type),
                          _buildDetailRow('Priority', ticket.priority),
                          _buildDetailRow(
                            'Created',
                            DateFormat('MMM d, y hh:mm a')
                                .format(ticket.createdAt),
                          ),
                          _buildDetailRow('Address', ticket.chargerAddress),
                          const SizedBox(height: 12),
                          Text(
                            'Description',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade600,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(ticket.description),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'open':
        return Colors.orange;
      case 'assigned':
        return Colors.blue;
      case 'in_progress':
        return Colors.purple;
      case 'resolved':
        return Colors.green;
      case 'closed':
        return Colors.grey;
      default:
        return Colors.grey;
    }
  }
}

class LiveTrackingScreen extends StatefulWidget {
  final String ticketId;

  const LiveTrackingScreen({
    Key? key,
    required this.ticketId,
  }) : super(key: key);

  @override
  State<LiveTrackingScreen> createState() => _LiveTrackingScreenState();
}

class _LiveTrackingScreenState extends State<LiveTrackingScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<TicketTrackingProvider>();
      final authProvider = context.read<AuthProvider>();

      // Start continuous tracking
      provider.startTracking(widget.ticketId, authProvider.token!);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Engineer Location'),
        elevation: 0,
      ),
      body: Consumer<TicketTrackingProvider>(
        builder: (context, provider, child) {
          final ticket = provider.ticketDetail;

          if (ticket?.engineerLocation == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.location_off,
                    size: 48,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Location unavailable',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Engineer location not yet available',
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            );
          }

          final location = ticket!.engineerLocation!;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Map placeholder
                Container(
                  width: double.infinity,
                  height: 300,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.location_on,
                          size: 48,
                          color: Colors.red,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Map integration needed\n${location.latitude.toStringAsFixed(4)}, ${location.longitude.toStringAsFixed(4)}',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Location Info
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Current Location',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Latitude',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  location.latitude.toStringAsFixed(6),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Longitude',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  location.longitude.toStringAsFixed(6),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        if (location.speed != null)
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Speed',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                              Text(
                                '${location.speed!.toStringAsFixed(1)} km/h',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Last Updated',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                            Text(
                              DateFormat('hh:mm:ss a')
                                  .format(location.timestamp),
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // ETA Card
                if (ticket.etaMinutes > 0)
                  Card(
                    color: Colors.blue.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(
                            Icons.schedule,
                            color: Colors.blue.shade600,
                            size: 32,
                          ),
                          const SizedBox(width: 16),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Estimated Arrival',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.blue.shade600,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${ticket.etaMinutes.toStringAsFixed(0)} minutes',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue.shade600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
