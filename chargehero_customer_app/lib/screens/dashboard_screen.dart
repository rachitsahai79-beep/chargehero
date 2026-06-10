import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:latlong2/latlong.dart';
import '../providers/auth_provider.dart';
import '../providers/charger_provider.dart';
import '../providers/ticket_tracking_provider.dart';
import 'ticket_details_screen.dart';
import 'location_picker_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> with TickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = context.read<AuthProvider>();
      final chargerProvider = context.read<ChargerProvider>();

      if (authProvider.token != null && authProvider.user != null) {
        chargerProvider.fetchChargers(authProvider.token!, authProvider.user!.id);
        chargerProvider.fetchTickets(authProvider.token!, authProvider.user!.id);
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ChargeHero'),
        elevation: 0,
        actions: [
          if (context.watch<AuthProvider>().user?.role == 'admin')
            IconButton(
              icon: const Icon(Icons.admin_panel_settings),
              tooltip: 'Admin',
              onPressed: () => Navigator.of(context).pushNamed('/admin'),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              context.read<AuthProvider>().logout();
              Navigator.of(context).pushReplacementNamed('/login');
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Chargers'),
            Tab(text: 'Tickets'),
          ],
        ),
      ),
      body: Consumer2<AuthProvider, ChargerProvider>(
        builder: (context, authProvider, chargerProvider, child) {
          return TabBarView(
            controller: _tabController,
            children: [
              _buildChargersTab(chargerProvider, authProvider),
              _buildTicketsTab(chargerProvider, authProvider),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          if (_tabController.index == 0) {
            _showRegisterChargerDialog();
          } else {
            _showRaiseTicketDialog();
          }
        },
        child: Icon(_tabController.index == 0 ? Icons.add : Icons.error),
      ),
    );
  }

  Widget _buildChargersTab(ChargerProvider chargerProvider, AuthProvider authProvider) {
    if (chargerProvider.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (chargerProvider.chargers.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.electrical_services,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              'No chargers yet',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Register your first charger',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () =>
          chargerProvider.fetchChargers(authProvider.token!, authProvider.user!.id),
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: chargerProvider.chargers.length,
        itemBuilder: (context, index) {
          final charger = chargerProvider.chargers[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: ListTile(
              leading: Icon(
                Icons.electrical_services,
                color: charger.status == 'active' ? Colors.green : Colors.grey,
              ),
              title: Text('${charger.brand} ${charger.model}'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text('SN: ${charger.serialNumber}'),
                  const SizedBox(height: 2),
                  Text(charger.address),
                ],
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Chip(
                    label: Text(charger.status),
                    backgroundColor: charger.status == 'active'
                        ? Colors.green.shade100
                        : Colors.grey.shade100,
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'edit') {
                        _showEditChargerDialog(charger);
                      } else if (value == 'delete') {
                        _confirmDeleteCharger(charger);
                      }
                    },
                    itemBuilder: (context) => const [
                      PopupMenuItem(value: 'edit', child: Text('Edit')),
                      PopupMenuItem(value: 'delete', child: Text('Delete')),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _confirmDeleteCharger(Charger charger) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete charger?'),
        content: Text('${charger.brand} ${charger.model} (SN: ${charger.serialNumber})'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    final auth = context.read<AuthProvider>();
    final chargerProvider = context.read<ChargerProvider>();
    final ok = await chargerProvider.deleteCharger(
      token: auth.token!,
      customerId: auth.user!.id,
      chargerId: charger.id,
    );
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ok ? 'Charger deleted' : (chargerProvider.error ?? 'Delete failed'))),
      );
    }
  }

  Widget _buildTicketsTab(ChargerProvider chargerProvider, AuthProvider authProvider) {
    if (chargerProvider.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (chargerProvider.tickets.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.check_circle,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              'No tickets',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'All systems operational',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () =>
          chargerProvider.fetchTickets(authProvider.token!, authProvider.user!.id),
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: chargerProvider.tickets.length,
        itemBuilder: (context, index) {
          final ticket = chargerProvider.tickets[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: ListTile(
              leading: Icon(
                Icons.task_alt,
                color: _getStatusColor(ticket.status),
              ),
              title: Text('Ticket #${ticket.id.substring(0, 8)}'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text(ticket.type),
                  const SizedBox(height: 2),
                  Text('Priority: ${ticket.priority}'),
                ],
              ),
              trailing: Chip(
                label: Text(ticket.status),
                backgroundColor: _getStatusColor(ticket.status).withOpacity(0.2),
              ),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => TicketDetailsScreen(
                      ticketId: ticket.id,
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showEditChargerDialog(Charger charger) {
    final serialController = TextEditingController(text: charger.serialNumber);
    final modelController = TextEditingController(text: charger.model);
    final brandController = TextEditingController(text: charger.brand);
    final addressController = TextEditingController(text: charger.address);
    final latController =
        TextEditingController(text: charger.latitude.toStringAsFixed(6));
    final lngController =
        TextEditingController(text: charger.longitude.toStringAsFixed(6));

    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Text('Edit Charger'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _field(serialController, 'Serial Number'),
                const SizedBox(height: 12),
                _field(brandController, 'Brand'),
                const SizedBox(height: 12),
                _field(modelController, 'Model'),
                const SizedBox(height: 12),
                _field(addressController, 'Address', maxLines: 2),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  icon: const Icon(Icons.location_on),
                  label: const Text('Change location on map'),
                  onPressed: () async {
                    LatLng? initial;
                    final la = double.tryParse(latController.text.trim());
                    final lo = double.tryParse(lngController.text.trim());
                    if (la != null && lo != null) initial = LatLng(la, lo);
                    final result = await Navigator.of(dialogContext).push<LatLng>(
                      MaterialPageRoute(
                        builder: (_) => LocationPickerScreen(initial: initial),
                      ),
                    );
                    if (result != null) {
                      setDialogState(() {
                        latController.text = result.latitude.toStringAsFixed(6);
                        lngController.text = result.longitude.toStringAsFixed(6);
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: _field(latController, 'Latitude', number: true)),
                    const SizedBox(width: 12),
                    Expanded(child: _field(lngController, 'Longitude', number: true)),
                  ],
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final lat = double.tryParse(latController.text.trim());
                final lng = double.tryParse(lngController.text.trim());
                if (lat == null || lng == null) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    const SnackBar(content: Text('Enter valid latitude/longitude')),
                  );
                  return;
                }
                final auth = context.read<AuthProvider>();
                final chargerProvider = context.read<ChargerProvider>();
                final ok = await chargerProvider.updateCharger(
                  token: auth.token!,
                  customerId: auth.user!.id,
                  chargerId: charger.id,
                  serialNumber: serialController.text.trim(),
                  model: modelController.text.trim(),
                  brand: brandController.text.trim(),
                  address: addressController.text.trim(),
                  latitude: lat,
                  longitude: lng,
                );
                if (ok && mounted) {
                  Navigator.pop(dialogContext);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Charger updated')),
                  );
                } else if (mounted) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    SnackBar(content: Text(chargerProvider.error ?? 'Update failed')),
                  );
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _field(TextEditingController c, String label,
      {int maxLines = 1, bool number = false}) {
    return TextField(
      controller: c,
      maxLines: maxLines,
      keyboardType: number
          ? const TextInputType.numberWithOptions(decimal: true, signed: true)
          : TextInputType.text,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }

  void _showRegisterChargerDialog() {
    final serialController = TextEditingController();
    final modelController = TextEditingController();
    final brandController = TextEditingController();
    final addressController = TextEditingController();
    final latController = TextEditingController();
    final lngController = TextEditingController();

    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Text('Register Charger'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: serialController,
                  decoration: InputDecoration(
                    labelText: 'Serial Number',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: brandController,
                  decoration: InputDecoration(
                    labelText: 'Brand',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: modelController,
                  decoration: InputDecoration(
                    labelText: 'Model',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: addressController,
                  decoration: InputDecoration(
                    labelText: 'Address',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  maxLines: 2,
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  icon: const Icon(Icons.location_on),
                  label: const Text('Pick location on map'),
                  onPressed: () async {
                    LatLng? initial;
                    final lat = double.tryParse(latController.text.trim());
                    final lng = double.tryParse(lngController.text.trim());
                    if (lat != null && lng != null) initial = LatLng(lat, lng);
                    final result = await Navigator.of(dialogContext).push<LatLng>(
                      MaterialPageRoute(
                        builder: (_) => LocationPickerScreen(initial: initial),
                      ),
                    );
                    if (result != null) {
                      // Push the selected lat/lng into the visible form fields.
                      setDialogState(() {
                        latController.text = result.latitude.toStringAsFixed(6);
                        lngController.text = result.longitude.toStringAsFixed(6);
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: latController,
                        decoration: InputDecoration(
                          labelText: 'Latitude',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: lngController,
                        decoration: InputDecoration(
                          labelText: 'Longitude',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: true,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final lat = double.tryParse(latController.text.trim());
                final lng = double.tryParse(lngController.text.trim());
                if (lat == null || lng == null) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    const SnackBar(
                      content: Text('Pick a location on the map or enter latitude/longitude'),
                    ),
                  );
                  return;
                }
                final authProvider = context.read<AuthProvider>();
                final chargerProvider = context.read<ChargerProvider>();

                final success = await chargerProvider.registerCharger(
                  token: authProvider.token!,
                  customerId: authProvider.user!.id,
                  serialNumber: serialController.text.trim(),
                  model: modelController.text.trim(),
                  brand: brandController.text.trim(),
                  address: addressController.text.trim(),
                  latitude: lat,
                  longitude: lng,
                );

                if (success && mounted) {
                  Navigator.pop(dialogContext);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Charger registered successfully')),
                  );
                } else if (mounted) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    SnackBar(content: Text(chargerProvider.error ?? 'Failed to register charger')),
                  );
                }
              },
              child: const Text('Register'),
            ),
          ],
        ),
      ),
    );
  }

  void _showRaiseTicketDialog() {
    final descriptionController = TextEditingController();
    String selectedType = 'issue';
    String selectedPriority = 'medium';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Raise Ticket'),
        content: StatefulBuilder(
          builder: (context, setState) => SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: selectedType,
                  items: ['issue', 'maintenance', 'question']
                      .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                      .toList(),
                  onChanged: (v) => setState(() => selectedType = v!),
                  decoration: InputDecoration(
                    labelText: 'Type',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedPriority,
                  items: ['low', 'medium', 'high', 'critical']
                      .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                      .toList(),
                  onChanged: (v) => setState(() => selectedPriority = v!),
                  decoration: InputDecoration(
                    labelText: 'Priority',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: descriptionController,
                  decoration: InputDecoration(
                    labelText: 'Description',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  maxLines: 3,
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final authProvider = context.read<AuthProvider>();
              final chargerProvider = context.read<ChargerProvider>();

              if (chargerProvider.chargers.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please register a charger first')),
                );
                return;
              }

              final success = await chargerProvider.raiseTicket(
                token: authProvider.token!,
                chargerId: chargerProvider.chargers.first.id,
                type: selectedType,
                priority: selectedPriority,
                description: descriptionController.text,
              );

              if (success && mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Ticket raised successfully')),
                );
              }
            },
            child: const Text('Raise'),
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
