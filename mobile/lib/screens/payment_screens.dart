import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../config.dart';
import '../state/session.dart';
import '../theme/tokens.dart';
import '../widgets/chrome.dart';

class PendingScreen extends StatefulWidget {
  const PendingScreen({super.key, required this.bookingId});

  final String bookingId;

  @override
  State<PendingScreen> createState() => _PendingScreenState();
}

class _PendingScreenState extends State<PendingScreen> {
  Timer? _timer;
  DateTime? _started;
  String? _hint;

  @override
  void initState() {
    super.initState();
    _started = DateTime.now();
    _timer = Timer.periodic(AppConfig.pollInterval, (_) => _poll());
    _poll();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _poll() async {
    final session = context.read<SessionController>();
    if (session.accessToken == null) return;
    try {
      final status = await session.api.bookingStatus(
        accessToken: session.accessToken!,
        bookingId: widget.bookingId,
      );
      if (!mounted) return;
      if (status.status == 'confirmed' && status.bookingCode != null) {
        _timer?.cancel();
        context.go('/pass/${status.bookingCode}');
        return;
      }
      if (status.status == 'failed' ||
          status.status == 'expired' ||
          status.status == 'cancelled') {
        _timer?.cancel();
        context.go('/book/failed');
        return;
      }
      if (DateTime.now().difference(_started!) > AppConfig.pollTimeout) {
        setState(
          () => _hint =
              'Still processing? Keep this screen open, or check My bookings.',
        );
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ScreenBody(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(color: MahgouzColors.courtGreen),
              const SizedBox(height: 24),
              Text(
                'Confirming payment…',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              Text(
                "Don't close this page.\nUsually takes a few seconds.",
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (_hint != null) ...[
                const SizedBox(height: 16),
                Text(_hint!, textAlign: TextAlign.center),
                TextButton(
                  onPressed: () => context.go('/bookings'),
                  child: const Text('My bookings'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class FailedScreen extends StatelessWidget {
  const FailedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ScreenBody(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircleAvatar(
                radius: 32,
                backgroundColor: Color(0x1AC0392B),
                child: Icon(Icons.close, color: Color(0xFFC0392B), size: 32),
              ),
              const SizedBox(height: 20),
              Text(
                "Payment didn't go through",
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Your slot has been released for others.',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              PrimaryButton(
                label: 'Try another slot',
                onPressed: () => context.go('/book'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => context.go('/'),
                child: const Text('Back to home'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
