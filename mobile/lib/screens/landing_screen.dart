import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config.dart';
import '../models.dart';
import '../state/session.dart';
import '../theme/tokens.dart';
import '../util/format.dart';
import '../widgets/booking_ui.dart';
import '../widgets/chrome.dart';

class LandingScreen extends StatefulWidget {
  const LandingScreen({super.key});

  @override
  State<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends State<LandingScreen> {
  List<Court> _courts = const [];
  final Map<String, int> _left = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final session = context.read<SessionController>();
    try {
      final courts = await session.api.courts();
      final date = formatIso(DateTime.now());
      final left = <String, int>{};
      for (final court in courts) {
        try {
          final grid = await session.api.slots(date: date, courtId: court.id);
          left[court.id] = grid.availableCount;
        } catch (_) {
          left[court.id] = 0;
        }
      }
      if (!mounted) return;
      setState(() {
        _courts = courts;
        _left
          ..clear()
          ..addAll(left);
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  void _book({String? period}) {
    final session = context.read<SessionController>();
    final extra = period == null ? '' : '?period=$period';
    if (session.isLoggedIn) {
      context.go('/book$extra');
    } else {
      context.push('/login?next=/book$extra');
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionController>();
    final dark = Theme.of(context).brightness == Brightness.dark;

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: ScreenBody(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(MahgouzRadii.lg),
                  child: AspectRatio(
                    aspectRatio: 4 / 3,
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Image.asset(BrandAssets.hero, fit: BoxFit.cover),
                        DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Color.fromRGBO(15, 26, 20, dark ? 0.35 : 0.05),
                                Color.fromRGBO(15, 26, 20, dark ? 0.82 : 0.55),
                              ],
                            ),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              Text(
                                'Book. Pay. Play.',
                                style: GoogleFonts.dmSans(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 32,
                                  height: 1.15,
                                  color: const Color(0xFFF4F7F5),
                                ),
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                AppConfig.locationLabel,
                                style: TextStyle(
                                  color: Color(0xE6F4F7F5),
                                  fontSize: 16,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                PrimaryButton(label: 'Book a court', onPressed: () => _book()),
                const SizedBox(height: 28),
                Text(
                  'How it works',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 12),
                Row(
                  children: const [
                    Expanded(
                      child: _StepCard(
                        n: '1',
                        icon: Icons.calendar_today_outlined,
                        title: 'Pick slot',
                        subtitle: 'Choose court and time',
                      ),
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: _StepCard(
                        n: '2',
                        icon: Icons.credit_card_outlined,
                        title: 'Pay',
                        subtitle: 'Secure payment in seconds',
                      ),
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: _StepCard(
                        n: '3',
                        icon: Icons.qr_code_2_rounded,
                        title: 'Pass',
                        subtitle: 'Show your pass and play',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                PromoBanner(onTap: () => _book(period: 'morning')),
                const SizedBox(height: 28),
                Text(
                  'Today at a glance',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 12),
                AppCard(
                  padding: EdgeInsets.zero,
                  child: _loading
                      ? const Padding(
                          padding: EdgeInsets.all(24),
                          child: Center(child: CircularProgressIndicator()),
                        )
                      : Column(
                          children: [
                            for (var i = 0; i < _courts.length; i++) ...[
                              if (i > 0) const Divider(height: 1),
                              ListTile(
                                leading: const Icon(
                                  Icons.circle,
                                  size: 10,
                                  color: MahgouzColors.courtGreen,
                                ),
                                title: Text(_courts[i].name),
                                trailing: Text(
                                  '${_left[_courts[i].id] ?? 0} slots left',
                                  style: const TextStyle(
                                    color: MahgouzColors.courtGreen,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                onTap: () => _book(),
                              ),
                            ],
                            if (_courts.isEmpty)
                              const Padding(
                                padding: EdgeInsets.all(20),
                                child: Text(
                                  'Two outdoor courts · 4 players each',
                                ),
                              ),
                          ],
                        ),
                ),
                const SizedBox(height: 28),
                Row(
                  children: [
                    const Icon(Icons.location_on_outlined, size: 18),
                    const SizedBox(width: 6),
                    Text(
                      'Sheikh Zayed, Egypt',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: () =>
                        launchUrl(Uri.parse(AppConfig.whatsappUrl)),
                    child: const Text('WhatsApp fallback'),
                  ),
                ),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: () => session.isStaff
                        ? context.go('/staff/bookings')
                        : context.push('/staff/login'),
                    child: const Text('Staff login'),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _StepCard extends StatelessWidget {
  const _StepCard({
    required this.n,
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final String n;
  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.fromLTRB(10, 14, 10, 14),
      child: Column(
        children: [
          Stack(
            clipBehavior: Clip.none,
            children: [
              Icon(icon, color: MahgouzColors.courtGreen, size: 22),
              Positioned(
                right: -10,
                top: -8,
                child: CircleAvatar(
                  radius: 8,
                  backgroundColor: MahgouzColors.courtGreen,
                  child: Text(
                    n,
                    style: const TextStyle(color: Colors.white, fontSize: 10),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
