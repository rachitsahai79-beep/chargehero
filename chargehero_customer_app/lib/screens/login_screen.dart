import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  bool _showOTP = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<AuthProvider>(
        builder: (context, authProvider, child) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 80),
                Icon(
                  Icons.bolt,
                  size: 64,
                  color: Colors.blue.shade600,
                ),
                const SizedBox(height: 24),
                Text(
                  'ChargeHero',
                  style: Theme.of(context).textTheme.headlineLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Customer App',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
                ),
                const SizedBox(height: 48),
                if (!_showOTP) _buildPhoneInput(context, authProvider) else _buildOTPInput(context, authProvider),
                const SizedBox(height: 24),
                if (authProvider.error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      border: Border.all(color: Colors.red.shade200),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error, color: Colors.red.shade700),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            authProvider.error!,
                            style: TextStyle(color: Colors.red.shade700),
                          ),
                        ),
                        IconButton(
                          icon: Icon(Icons.close, color: Colors.red.shade700),
                          onPressed: authProvider.clearError,
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildPhoneInput(BuildContext context, AuthProvider authProvider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _phoneController,
          decoration: InputDecoration(
            labelText: 'Phone Number',
            hintText: '+919876543210',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            prefixIcon: const Icon(Icons.phone),
          ),
          keyboardType: TextInputType.phone,
          enabled: !authProvider.isLoading,
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: authProvider.isLoading
              ? null
              : () async {
                  final phone = _phoneController.text.trim();
                  if (phone.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please enter your phone number')),
                    );
                    return;
                  }

                  final success = await authProvider.sendLoginOTP(phone);
                  if (success) {
                    setState(() => _showOTP = true);
                  }
                },
          child: authProvider.isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Send OTP'),
        ),
      ],
    );
  }

  Widget _buildOTPInput(BuildContext context, AuthProvider authProvider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Enter OTP sent to ${_phoneController.text}',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Colors.grey.shade600,
          ),
        ),
        const SizedBox(height: 24),
        TextField(
          controller: _otpController,
          decoration: InputDecoration(
            labelText: 'OTP',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            prefixIcon: const Icon(Icons.lock),
          ),
          keyboardType: TextInputType.number,
          maxLength: 6,
          enabled: !authProvider.isLoading,
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: authProvider.isLoading
              ? null
              : () async {
                  final otp = _otpController.text.trim();
                  if (otp.isEmpty || otp.length != 6) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please enter a valid 6-digit OTP')),
                    );
                    return;
                  }

                  await authProvider.verifyLoginOTP(
                    phone: _phoneController.text.trim(),
                    otp: otp,
                  );

                  if (authProvider.isAuthenticated && mounted) {
                    Navigator.of(context).pushReplacementNamed('/home');
                  }
                },
          child: authProvider.isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Login'),
        ),
        const SizedBox(height: 12),
        TextButton(
          onPressed: () => setState(() => _showOTP = false),
          child: const Text('Change Phone Number'),
        ),
      ],
    );
  }
}
