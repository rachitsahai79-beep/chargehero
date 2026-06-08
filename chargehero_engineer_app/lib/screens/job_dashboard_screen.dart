// chargehero_engineer_app/lib/screens/job_dashboard_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/job_provider.dart';
import '../widgets/job_card.dart';

class JobDashboardScreen extends StatefulWidget {
  const JobDashboardScreen({Key? key}) : super(key: key);

  @override
  State<JobDashboardScreen> createState() => _JobDashboardScreenState();
}

class _JobDashboardScreenState extends State<JobDashboardScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    // Fetch open jobs on load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<JobProvider>().fetchOpenJobs();
      context.read<JobProvider>().fetchMyJobs();
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
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Available Jobs', icon: Icon(Icons.assignment_ind)),
            Tab(text: 'My Jobs', icon: Icon(Icons.work)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildAvailableJobsTab(),
          _buildMyJobsTab(),
        ],
      ),
    );
  }

  Widget _buildAvailableJobsTab() {
    return Consumer<JobProvider>(
      builder: (context, jobProvider, child) {
        if (jobProvider.isLoading) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        if (jobProvider.openJobs.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.inbox,
                  size: 64,
                  color: Colors.grey[300],
                ),
                const SizedBox(height: 16),
                Text(
                  'No open jobs available',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Pull down to refresh',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: () => jobProvider.fetchOpenJobs(),
          child: ListView.builder(
            itemCount: jobProvider.openJobs.length,
            padding: const EdgeInsets.all(16),
            itemBuilder: (context, index) {
              final job = jobProvider.openJobs[index];
              return JobCard(
                job: job,
                onTap: () {
                  jobProvider.selectJob(job);
                  Navigator.pushNamed(context, '/job-details');
                },
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildMyJobsTab() {
    return Consumer<JobProvider>(
      builder: (context, jobProvider, child) {
        if (jobProvider.myJobs.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.check_circle_outline,
                  size: 64,
                  color: Colors.grey[300],
                ),
                const SizedBox(height: 16),
                Text(
                  'No assigned jobs',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Accept jobs from available list',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          itemCount: jobProvider.myJobs.length,
          padding: const EdgeInsets.all(16),
          itemBuilder: (context, index) {
            final job = jobProvider.myJobs[index];
            return JobCard(
              job: job,
              onTap: () {
                jobProvider.selectJob(job);
                Navigator.pushNamed(context, '/job-details');
              },
            );
          },
        );
      },
    );
  }
}
