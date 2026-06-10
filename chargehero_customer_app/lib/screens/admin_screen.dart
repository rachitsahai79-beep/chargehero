import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/admin_provider.dart';

/// Admin-only dashboard: all chargers, engineers, and summary stats.
/// Reachable from the main dashboard when the logged-in user has role=admin.
class AdminScreen extends StatefulWidget {
  const AdminScreen({Key? key}) : super(key: key);

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      if (auth.token != null) {
        context.read<AdminProvider>().fetchAll(auth.token!);
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
        title: const Text('Admin'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Chargers'),
            Tab(text: 'Engineers'),
            Tab(text: 'Dashboard'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              final auth = context.read<AuthProvider>();
              if (auth.token != null) {
                context.read<AdminProvider>().fetchAll(auth.token!);
              }
            },
          ),
        ],
      ),
      body: Consumer<AdminProvider>(
        builder: (context, admin, child) {
          if (admin.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          return TabBarView(
            controller: _tabController,
            children: [
              _chargersTab(admin),
              _engineersTab(admin),
              _dashboardTab(admin),
            ],
          );
        },
      ),
    );
  }

  Widget _chargersTab(AdminProvider admin) {
    if (admin.allChargers.isEmpty) {
      return const Center(child: Text('No chargers'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: admin.allChargers.length,
      itemBuilder: (context, i) {
        final c = admin.allChargers[i];
        return Card(
          child: ListTile(
            leading: Icon(
              Icons.electrical_services,
              color: c.status == 'active' ? Colors.green : Colors.grey,
            ),
            title: Text('${c.brand} ${c.model}'),
            subtitle: Text(
              'SN: ${c.serialNumber}\n${c.address}\n'
              '(${c.latitude.toStringAsFixed(4)}, ${c.longitude.toStringAsFixed(4)})',
            ),
            isThreeLine: true,
            trailing: Chip(label: Text(c.status)),
          ),
        );
      },
    );
  }

  Widget _engineersTab(AdminProvider admin) {
    if (admin.engineers.isEmpty) {
      return const Center(child: Text('No engineers'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: admin.engineers.length,
      itemBuilder: (context, i) {
        final e = admin.engineers[i];
        final name = (e['name'] ?? e['full_name'] ?? e['business_name'] ?? 'Engineer').toString();
        final status = (e['status'] ?? e['registration_status'] ?? '').toString();
        return Card(
          child: ListTile(
            leading: const Icon(Icons.engineering),
            title: Text(name),
            subtitle: Text(e['work_area']?.toString() ?? e['email']?.toString() ?? ''),
            trailing: status.isEmpty ? null : Chip(label: Text(status)),
          ),
        );
      },
    );
  }

  Widget _dashboardTab(AdminProvider admin) {
    final d = admin.dashboard;
    if (d == null) {
      return const Center(child: Text('No dashboard data'));
    }
    final entries = d.entries.toList();
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: entries.length,
      itemBuilder: (context, i) {
        final entry = entries[i];
        return Card(
          child: ListTile(
            title: Text(_humanize(entry.key)),
            trailing: Text(
              entry.value is Map || entry.value is List
                  ? entry.value.toString()
                  : '${entry.value}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        );
      },
    );
  }

  String _humanize(String key) {
    return key
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}
