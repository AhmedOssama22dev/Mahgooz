import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../state/session.dart';
import '../widgets/cards.dart';
import '../widgets/chrome.dart';

class BookingsScreen extends StatefulWidget {
  const BookingsScreen({super.key});

  @override
  State<BookingsScreen> createState() => _BookingsScreenState();
}

class _BookingsScreenState extends State<BookingsScreen> {
  BookingList? _list;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final session = context.read<SessionController>();
    if (session.accessToken == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final list = await session.api.myBookings(session.accessToken!);
      if (!mounted) return;
      setState(() => _list = list);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final list = _list;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'My bookings',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
              ),
              TextButton(
                onPressed: () => context.go('/book'),
                child: const Text('+ Book'),
              ),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _load,
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
                    children: [
                      if (_error != null) Text(_error!),
                      if (list == null ||
                          (list.upcoming.isEmpty && list.past.isEmpty)) ...[
                        const SizedBox(height: 48),
                        Text(
                          'No bookings yet',
                          style: Theme.of(context).textTheme.headlineMedium,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Book your first court in under a minute.',
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 20),
                        PrimaryButton(
                          label: 'Book a court',
                          onPressed: () => context.go('/book'),
                        ),
                      ] else ...[
                        if (list.upcoming.isNotEmpty) ...[
                          Text(
                            'Upcoming',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 10),
                          for (final b in list.upcoming) ...[
                            BookingCard(booking: b),
                            const SizedBox(height: 10),
                          ],
                          const SizedBox(height: 12),
                        ],
                        if (list.past.isNotEmpty) ...[
                          Text(
                            'Past',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 10),
                          for (final b in list.past) ...[
                            BookingCard(booking: b, past: true),
                            const SizedBox(height: 10),
                          ],
                        ],
                      ],
                    ],
                  ),
          ),
        ),
      ],
    );
  }
}
