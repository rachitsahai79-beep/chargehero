import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/earnings_provider.dart';

class EarningsDashboardScreen extends StatefulWidget {
  final String engineerId;

  const EarningsDashboardScreen({
    Key? key,
    required this.engineerId,
  }) : super(key: key);

  @override
  State<EarningsDashboardScreen> createState() => _EarningsDashboardScreenState();
}

class _EarningsDashboardScreenState extends State<EarningsDashboardScreen> with TickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<EarningsProvider>();
      provider.fetchEarnings(widget.engineerId);
      provider.fetchJobHistory(widget.engineerId);
      provider.fetchStatistics(widget.engineerId);
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
        title: const Text('Earnings'),
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'History'),
            Tab(text: 'Statistics'),
          ],
        ),
      ),
      body: Consumer<EarningsProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.totalEarnings == 0) {
            return const Center(child: CircularProgressIndicator());
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildOverviewTab(provider),
              _buildHistoryTab(provider),
              _buildStatisticsTab(provider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildOverviewTab(EarningsProvider provider) {
    final currencyFormat = NumberFormat.currency(symbol: '₹');

    return RefreshIndicator(
      onRefresh: () async {
        await provider.fetchEarnings(widget.engineerId);
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Total Earnings Card
            Card(
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Total Earnings',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      currencyFormat.format(provider.totalEarnings),
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Earnings Summary Grid
            Row(
              children: [
                Expanded(
                  child: _buildEarningsCard(
                    title: 'This Month',
                    amount: provider.monthlyEarnings,
                    currencyFormat: currencyFormat,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildEarningsCard(
                    title: 'Pending',
                    amount: provider.pendingEarnings,
                    currencyFormat: currencyFormat,
                    isPending: true,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Performance Metrics
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    label: 'Completed Jobs',
                    value: '${provider.completedJobs}',
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    label: 'Avg Rating',
                    value: '${provider.averageRating.toStringAsFixed(1)}/5',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Payment History Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  _tabController.animateTo(1);
                },
                child: const Text('View Job History'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEarningsCard({
    required String title,
    required double amount,
    required NumberFormat currencyFormat,
    bool isPending = false,
  }) {
    return Card(
      elevation: 1,
      color: isPending ? Colors.orange.shade50 : Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade600,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              currencyFormat.format(amount),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: isPending ? Colors.orange : Colors.blue,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard({
    required String label,
    required String value,
  }) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade600,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryTab(EarningsProvider provider) {
    if (provider.jobHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history,
              size: 48,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              'No job history yet',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    final currencyFormat = NumberFormat.currency(symbol: '₹');

    return RefreshIndicator(
      onRefresh: () async {
        await provider.fetchJobHistory(widget.engineerId);
      },
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: provider.jobHistory.length,
        itemBuilder: (context, index) {
          final job = provider.jobHistory[index];
          final createdAt = DateTime.parse(job['created_at'] ?? DateTime.now().toIso8601String());
          final dateFormat = DateFormat('MMM d, y - hh:mm a');

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 6),
            child: ListTile(
              title: Text(
                'Job #${job['ticket_id']?.substring(0, 8) ?? 'Unknown'}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text(
                    'Completed: ${dateFormat.format(createdAt)}',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Time: ${job['resolution_time_minutes']} mins',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                  if (job['rating_by_customer'] != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.star, size: 16, color: Colors.amber),
                        const SizedBox(width: 4),
                        Text(
                          '${job['rating_by_customer']}/5',
                          style: const TextStyle(fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
              trailing: Text(
                currencyFormat.format(job['amount'] ?? 0.0),
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.green,
                ),
              ),
              onTap: () {
                _showJobDetails(job);
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatisticsTab(EarningsProvider provider) {
    final stats = provider.statistics;

    if (stats.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.bar_chart,
              size: 48,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              'No statistics available',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        await provider.fetchStatistics(widget.engineerId);
      },
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Performance Statistics',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            _buildStatCard(
              label: 'Total Reports',
              value: '${stats['total_reports'] ?? 0}',
            ),
            const SizedBox(height: 12),

            _buildStatCard(
              label: 'Avg Resolution Time',
              value: '${stats['average_resolution_time_minutes']?.toStringAsFixed(1) ?? 0} mins',
            ),
            const SizedBox(height: 12),

            _buildStatCard(
              label: 'Avg Customer Rating',
              value: '${stats['average_customer_rating']?.toStringAsFixed(1) ?? 0}/5',
            ),
            const SizedBox(height: 12),

            _buildStatCard(
              label: 'Rated Reports',
              value: '${stats['rated_reports'] ?? 0}',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard({
    required String label,
    required String value,
  }) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade700,
              ),
            ),
            Text(
              value,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showJobDetails(Map<String, dynamic> job) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Job Details',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            _detailRow('Ticket ID', job['ticket_id'] ?? 'N/A'),
            _detailRow('Work Description', job['work_description'] ?? 'N/A'),
            _detailRow(
              'Spare Parts Used',
              (job['spare_parts_used'] as List?)?.join(', ') ?? 'None',
            ),
            _detailRow('Resolution Time', '${job['resolution_time_minutes']} minutes'),
            if (job['rating_by_customer'] != null)
              _detailRow('Customer Rating', '${job['rating_by_customer']}/5 ⭐'),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
