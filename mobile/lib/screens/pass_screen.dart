import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../models.dart';
import '../state/session.dart';
import '../theme/tokens.dart';
import '../util/format.dart';
import '../widgets/booking_ui.dart';
import '../widgets/chrome.dart';

class PassScreen extends StatefulWidget {
  const PassScreen({super.key, required this.code});

  final String code;

  @override
  State<PassScreen> createState() => _PassScreenState();
}

class _PassScreenState extends State<PassScreen> {
  Pass? _pass;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final pass = await context.read<SessionController>().api.publicPass(
        widget.code,
      );
      if (!mounted) return;
      setState(() => _pass = pass);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionController>();
    final pass = _pass;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Booking pass'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              session.isLoggedIn ? context.go('/bookings') : context.go('/'),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : pass == null
          ? ScreenBody(
              child: Center(
                child: Text(_error ?? 'No paid booking for this code.'),
              ),
            )
          : ScreenBody(
              child: ListView(
                children: [
                  Center(child: StatusBadge(status: pass.status)),
                  const SizedBox(height: 20),
                  Center(
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(MahgouzRadii.md),
                      ),
                      child: QrImageView(
                        data: pass.qrPayload,
                        size: 200,
                        backgroundColor: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Center(
                    child: Text(
                      pass.bookingCode,
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 28,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 2,
                      ),
                    ),
                  ),
                  Center(
                    child: TextButton(
                      onPressed: () async {
                        await Clipboard.setData(
                          ClipboardData(text: pass.bookingCode),
                        );
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Code copied')),
                        );
                      },
                      child: const Text('Copy code'),
                    ),
                  ),
                  const Divider(height: 32),
                  Text(
                    pass.court.name,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 6),
                  Text(formatDayLong(DateTime.parse(pass.date))),
                  Text('${pass.startTime} – ${pass.endTime}'),
                  Text(
                    '${pass.bookerName} · ${pass.attendeeNames.length} players',
                  ),
                  Text('Paid · ${formatEgp(pass.priceEgp)}'),
                  const SizedBox(height: 24),
                  Text(
                    'Show this to staff on arrival',
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
    );
  }
}
