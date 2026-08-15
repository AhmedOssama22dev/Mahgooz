import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../api/errors.dart';
import '../models.dart';
import '../state/session.dart';
import '../theme/tokens.dart';
import '../util/format.dart';
import '../widgets/cards.dart';
import '../widgets/chrome.dart';

class StaffLoginScreen extends StatefulWidget {
  const StaffLoginScreen({super.key});

  @override
  State<StaffLoginScreen> createState() => _StaffLoginScreenState();
}

class _StaffLoginScreenState extends State<StaffLoginScreen> {
  String _pin = '';
  bool _error = false;
  bool _loading = false;

  Future<void> _submit() async {
    if (_pin.length != 4) return;
    setState(() {
      _loading = true;
      _error = false;
    });
    try {
      await context.read<SessionController>().staffLogin(_pin);
      if (!mounted) return;
      context.go('/staff/bookings');
    } on ApiException {
      setState(() {
        _error = true;
        _pin = '';
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mahgouz Staff'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.go('/'),
        ),
      ),
      body: ScreenBody(
        child: Column(
          children: [
            const SizedBox(height: 24),
            Text('Enter PIN', style: Theme.of(context).textTheme.headlineLarge),
            const SizedBox(height: 8),
            Text(
              _error ? 'Incorrect PIN' : 'Front desk access',
              style: TextStyle(
                color: _error
                    ? MahgouzColors.error
                    : Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 32),
            if (_loading)
              const CircularProgressIndicator()
            else
              PinPad(
                value: _pin,
                error: _error,
                onChanged: (v) => setState(() {
                  _pin = v;
                  _error = false;
                }),
                onSubmit: _submit,
              ),
            const SizedBox(height: 24),
            Text(
              'Demo PIN: 1234',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}

class StaffLookupScreen extends StatefulWidget {
  const StaffLookupScreen({super.key});

  @override
  State<StaffLookupScreen> createState() => _StaffLookupScreenState();
}

class _StaffLookupScreenState extends State<StaffLookupScreen> {
  final _code = TextEditingController();
  List<StaffBooking> _next = const [];

  @override
  void initState() {
    super.initState();
    _loadNext();
  }

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _loadNext() async {
    final session = context.read<SessionController>();
    if (session.staffToken == null) return;
    try {
      final day = await session.api.staffBookings(
        staffToken: session.staffToken!,
        date: formatIso(DateTime.now()),
      );
      final upcoming = day.bookings
          .where((b) => b.status == 'confirmed')
          .take(3)
          .toList();
      if (!mounted) return;
      setState(() => _next = upcoming);
    } catch (_) {}
  }

  void _search() {
    final code = _code.text.trim().toUpperCase();
    if (code.isEmpty) return;
    context.push('/staff/pass/$code');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Look up a booking'),
        actions: [
          TextButton(
            onPressed: () => context.go('/staff/bookings'),
            child: const Text("Today's bookings"),
          ),
        ],
      ),
      body: ScreenBody(
        child: ListView(
          children: [
            TextField(
              controller: _code,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Enter code',
                hintText: 'MGZ-7F42K',
              ),
              onSubmitted: (_) => _search(),
            ),
            const SizedBox(height: 16),
            PrimaryButton(label: 'Search', onPressed: _search),
            const SizedBox(height: 28),
            Text(
              'Next arrivals',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 10),
            if (_next.isEmpty)
              Text(
                'No upcoming check-ins.',
                style: Theme.of(context).textTheme.bodyMedium,
              )
            else
              for (final b in _next) ...[
                AppCard(
                  onTap: () => context.push('/staff/pass/${b.bookingCode}'),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${b.startTime} ${b.courtName} · ${b.bookingCode}',
                            ),
                            Text(
                              'Paid · not redeemed',
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
              ],
          ],
        ),
      ),
    );
  }
}

class StaffBookingsScreen extends StatefulWidget {
  const StaffBookingsScreen({super.key});

  @override
  State<StaffBookingsScreen> createState() => _StaffBookingsScreenState();
}

class _StaffBookingsScreenState extends State<StaffBookingsScreen> {
  DateTime _date = DateTime.now();
  StaffDay? _day;
  String _filter = 'all';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _date = DateTime(_date.year, _date.month, _date.day);
    _load();
  }

  Future<void> _load() async {
    final session = context.read<SessionController>();
    if (session.staffToken == null) return;
    setState(() => _loading = true);
    try {
      final day = await session.api.staffBookings(
        staffToken: session.staffToken!,
        date: formatIso(_date),
      );
      if (!mounted) return;
      setState(() => _day = day);
    } catch (_) {
      if (!mounted) return;
      setState(() => _day = const StaffDay(date: '', bookings: []));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<StaffBooking> get _filtered {
    final all = _day?.bookings ?? const [];
    return all.where((b) {
      switch (_filter) {
        case 'court-1':
          return b.courtName == 'Court 1';
        case 'court-2':
          return b.courtName == 'Court 2';
        case 'paid':
          return b.status == 'confirmed';
        case 'redeemed':
          return b.status == 'redeemed';
        default:
          return true;
      }
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final bookings = _day?.bookings ?? const [];
    final ready = bookings.where((b) => b.status == 'confirmed').length;
    final done = bookings.where((b) => b.status == 'redeemed').length;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Today's bookings"),
        actions: [
          IconButton(
            tooltip: 'Lookup',
            onPressed: () => context.push('/staff'),
            icon: const Icon(Icons.search),
          ),
          IconButton(
            tooltip: 'Log out',
            onPressed: () async {
              await context.read<SessionController>().staffLogout();
              if (context.mounted) context.go('/');
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Row(
              children: [
                IconButton(
                  onPressed: () {
                    setState(
                      () => _date = _date.subtract(const Duration(days: 1)),
                    );
                    _load();
                  },
                  icon: const Icon(Icons.chevron_left),
                ),
                Expanded(
                  child: Text(
                    formatDayLong(_date),
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                IconButton(
                  onPressed: () {
                    setState(() => _date = _date.add(const Duration(days: 1)));
                    _load();
                  },
                  icon: const Icon(Icons.chevron_right),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              '${bookings.length} booked  ·  $done checked in  ·  $ready upcoming',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                for (final f in [
                  ('all', 'All'),
                  ('court-1', 'Court 1'),
                  ('court-2', 'Court 2'),
                  ('paid', 'Paid'),
                  ('redeemed', 'Redeemed'),
                ])
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(f.$2),
                      selected: _filter == f.$1,
                      onSelected: (_) => setState(() => _filter = f.$1),
                      selectedColor: MahgouzColors.courtGreenLight,
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
                    itemCount: _filtered.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, i) {
                      final b = _filtered[i];
                      final readyToRedeem = b.status == 'confirmed';
                      return AppCard(
                        onTap: () =>
                            context.push('/staff/pass/${b.bookingCode}'),
                        child: Row(
                          children: [
                            SizedBox(
                              width: 56,
                              child: Text(
                                b.startTime,
                                style: GoogleFonts.dmSans(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${b.courtName} · ${b.bookerName}'),
                                  Text(
                                    b.bookingCode,
                                    style: GoogleFonts.jetBrainsMono(
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Text(
                              readyToRedeem ? 'Ready' : 'Done',
                              style: TextStyle(
                                color: readyToRedeem
                                    ? MahgouzColors.courtGreen
                                    : MahgouzColors.redeemed,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class StaffPassScreen extends StatefulWidget {
  const StaffPassScreen({super.key, required this.code});

  final String code;

  @override
  State<StaffPassScreen> createState() => _StaffPassScreenState();
}

class _StaffPassScreenState extends State<StaffPassScreen> {
  Pass? _pass;
  String? _error;
  bool _loading = true;
  bool _redeeming = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final session = context.read<SessionController>();
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final pass = await session.api.staffPass(
        staffToken: session.staffToken!,
        code: widget.code,
      );
      if (!mounted) return;
      setState(() => _pass = pass);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _redeem() async {
    final session = context.read<SessionController>();
    setState(() => _redeeming = true);
    try {
      final pass = await session.api.redeem(
        staffToken: session.staffToken!,
        code: widget.code,
      );
      if (!mounted) return;
      setState(() => _pass = pass);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(e.message)));
      await _load();
    } finally {
      if (mounted) setState(() => _redeeming = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pass = _pass;
    final canRedeem = pass?.canRedeem == true || pass?.status == 'confirmed';
    return Scaffold(
      appBar: AppBar(title: Text(widget.code.toUpperCase())),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ScreenBody(
              child: pass == null
                  ? Center(child: Text(_error ?? 'No booking for this code'))
                  : ListView(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: canRedeem && pass.status != 'redeemed'
                                ? MahgouzColors.courtGreenLight
                                : Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Theme.of(context).dividerColor,
                            ),
                          ),
                          child: Text(
                            pass.status == 'redeemed'
                                ? 'REDEEMED${pass.redeemedAt != null ? ' at ${TimeOfDay.fromDateTime(pass.redeemedAt!).format(context)}' : ''}'
                                : 'PAID — Ready',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          pass.court.name,
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        Text(
                          '${formatDay(DateTime.parse(pass.date))} · ${pass.startTime}–${pass.endTime}',
                        ),
                        const SizedBox(height: 8),
                        Text(
                          pass.bookerName,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        if (pass.bookerPhone != null) Text(pass.bookerPhone!),
                        Text('${pass.attendeeNames.length} players'),
                        Text(
                          '${formatEgp(pass.priceEgp)}${pass.paymobTransactionId != null ? ' · Paymob #${pass.paymobTransactionId}' : ''}',
                        ),
                        const SizedBox(height: 28),
                        PrimaryButton(
                          label: pass.status == 'redeemed'
                              ? 'Already checked in'
                              : 'Redeem check-in',
                          loading: _redeeming,
                          onPressed: pass.status == 'redeemed' ? null : _redeem,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Redeeming marks this pass as used. Cannot undo.',
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
            ),
    );
  }
}
