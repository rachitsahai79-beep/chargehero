import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/auth_provider.dart';
import '../providers/checklist_provider.dart';

class ChecklistApprovalScreen extends StatefulWidget {
  const ChecklistApprovalScreen({Key? key}) : super(key: key);

  @override
  State<ChecklistApprovalScreen> createState() => _ChecklistApprovalScreenState();
}

class _ChecklistApprovalScreenState extends State<ChecklistApprovalScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = context.read<AuthProvider>();
      final checklistProvider = context.read<ChecklistProvider>();
      checklistProvider.fetchPendingChecklists(authProvider.token!);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Checklist Approvals'),
        elevation: 0,
      ),
      body: Consumer2<AuthProvider, ChecklistProvider>(
        builder: (context, authProvider, checklistProvider, child) {
          if (checklistProvider.isLoading && checklistProvider.pendingChecklists.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (checklistProvider.pendingChecklists.isEmpty) {
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
                    'No pending approvals',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'All checklists have been reviewed',
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => checklistProvider.fetchPendingChecklists(authProvider.token!),
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: checklistProvider.pendingChecklists.length,
              itemBuilder: (context, index) {
                final checklist = checklistProvider.pendingChecklists[index];
                return ChecklistCard(
                  checklist: checklist,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ChecklistDetailScreen(
                          checklist: checklist,
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class ChecklistCard extends StatelessWidget {
  final ChecklistResponse checklist;
  final VoidCallback onTap;

  const ChecklistCard({
    Key? key,
    required this.checklist,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ticket #${checklist.ticketId.substring(0, 8)}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Engineer: ${checklist.engineerName}',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                  Chip(
                    label: Text('${checklist.completedItems}/${checklist.totalItems}'),
                    backgroundColor: Colors.blue.shade100,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: checklist.completionPercentage / 100,
                  minHeight: 6,
                  backgroundColor: Colors.grey.shade300,
                  valueColor: AlwaysStoppedAnimation(
                    _getStatusColor(checklist.completionPercentage),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${checklist.completionPercentage.toStringAsFixed(0)}% Complete',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                  Text(
                    DateFormat('MMM d, y').format(checklist.submittedAt),
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getStatusColor(double percentage) {
    if (percentage >= 90) return Colors.green;
    if (percentage >= 70) return Colors.blue;
    if (percentage >= 50) return Colors.orange;
    return Colors.red;
  }
}

class ChecklistDetailScreen extends StatefulWidget {
  final ChecklistResponse checklist;

  const ChecklistDetailScreen({
    Key? key,
    required this.checklist,
  }) : super(key: key);

  @override
  State<ChecklistDetailScreen> createState() => _ChecklistDetailScreenState();
}

class _ChecklistDetailScreenState extends State<ChecklistDetailScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Checklist #${widget.checklist.ticketId.substring(0, 8)}'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Engineer Info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Engineer',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.checklist.engineerName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Completion Status
            Card(
              color: Colors.blue.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Completion Status',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    const SizedBox(height: 12),
                    LinearProgressIndicator(
                      value: widget.checklist.completionPercentage / 100,
                      minHeight: 8,
                      backgroundColor: Colors.grey.shade300,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${widget.checklist.completedItems}/${widget.checklist.totalItems} items',
                        ),
                        Text(
                          '${widget.checklist.completionPercentage.toStringAsFixed(1)}%',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Checklist Items
            Text(
              'Checklist Items',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            ...widget.checklist.items.map((item) => ChecklistItemWidget(item: item)).toList(),
            const SizedBox(height: 24),

            // Action Buttons
            Consumer<ChecklistProvider>(
              builder: (context, checklistProvider, child) {
                return Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => _rejectChecklist(context, checklistProvider),
                        icon: const Icon(Icons.close),
                        label: const Text('Reject'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red.shade400,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => _approveChecklist(context, checklistProvider),
                        icon: const Icon(Icons.check),
                        label: const Text('Approve'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green.shade400,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _approveChecklist(BuildContext context, ChecklistProvider provider) async {
    final authProvider = context.read<AuthProvider>();
    final success = await provider.approveChecklist(
      widget.checklist.id,
      authProvider.token!,
    );

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Checklist approved')),
      );
      Navigator.pop(context);
    }
  }

  void _rejectChecklist(BuildContext context, ChecklistProvider provider) {
    final reasonController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reject Checklist'),
        content: TextField(
          controller: reasonController,
          decoration: InputDecoration(
            labelText: 'Reason for rejection',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final authProvider = context.read<AuthProvider>();
              final success = await provider.rejectChecklist(
                widget.checklist.id,
                reasonController.text,
                authProvider.token!,
              );

              if (success && mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Checklist rejected')),
                );
                Navigator.pop(context);
              }
            },
            child: const Text('Reject'),
          ),
        ],
      ),
    );
  }
}

class ChecklistItemWidget extends StatelessWidget {
  final ChecklistItem item;

  const ChecklistItemWidget({
    Key? key,
    required this.item,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        title: Row(
          children: [
            if (item.passed != null)
              Icon(
                item.passed! ? Icons.check_circle : Icons.cancel,
                color: item.passed! ? Colors.green : Colors.red,
                size: 20,
              ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(item.description),
            ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (item.responseValue != null) ...[
                  Text(
                    'Response',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 4),
                  Text(item.responseValue!),
                  const SizedBox(height: 12),
                ],
                if (item.notes != null && item.notes!.isNotEmpty) ...[
                  Text(
                    'Notes',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 4),
                  Text(item.notes!),
                  const SizedBox(height: 12),
                ],
                if (item.mediaUrls.isNotEmpty) ...[
                  Text(
                    'Attachments',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: item.mediaUrls
                        .map((url) => MediaPreviewWidget(url: url))
                        .toList(),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class MediaPreviewWidget extends StatelessWidget {
  final String url;

  const MediaPreviewWidget({
    Key? key,
    required this.url,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isImage = url.contains(RegExp(r'\.(jpg|jpeg|png|webp)'));
    final isVideo = url.contains(RegExp(r'\.(mp4|mov|avi)'));

    return GestureDetector(
      onTap: () {
        // Open media preview dialog
        _showMediaPreview(context);
      },
      child: Container(
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Icon(
            isImage ? Icons.image : isVideo ? Icons.videocam : Icons.attachment,
            color: Colors.grey.shade600,
          ),
        ),
      ),
    );
  }

  void _showMediaPreview(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Media Preview'),
        content: Container(
          width: 300,
          height: 300,
          color: Colors.grey.shade300,
          child: Center(
            child: Icon(
              Icons.media_bluetooth_on,
              size: 64,
              color: Colors.grey.shade600,
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
