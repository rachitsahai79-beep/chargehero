import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/charger_provider.dart';

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

      if (authProvider.token != null) {
        chargerProvider.fetchChargers(authProvider.token!);
        chargerProvider.fetchTickets(authProvider.token!);
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
              Icons.ev_charger,
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
      onRefresh: () => chargerProvider.fetchChargers(authProvider.token!),
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: chargerProvider.chargers.length,
        itemBuilder: (context, index) {
          final charger = chargerProvider.chargers[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: ListTile(
              leading: Icon(
                Icons.ev_charger,
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
              trailing: Chip(
                label: Text(charger.status),
                backgroundColor: charger.status == 'active'
                    ? Colors.green.shade100
                    : Colors.grey.shade100,
              ),
              onTap: () {
                // Navigate to charger details
              },
            ),
          );
        },
      ),
    );
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
      onRefresh: () => chargerProvider.fetchTickets(authProvider.token!),
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
                // Navigate to ticket details
              },
            ),
          );
        },
      ),
    );
  }

  void _showRegisterChargerDialog() {
    final serialController = TextEditingController();
    final modelController = TextEditingController();
    final brandController = TextEditingController();
    final addressController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
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
                maxLines: 3,
              ),
            ],
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

              final success = await chargerProvider.registerCharger(
                token: authProvider.token!,
                serialNumber: serialController.text,
                model: modelController.text,
                brand: brandController.text,
                address: addressController.text,
              );

              if (success && mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Charger registered successfully')),
                );
              }
            },
            child: const Text('Register'),
          ),
        ],
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
