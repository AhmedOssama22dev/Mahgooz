import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/errors.dart';
import '../models.dart';
import '../state/session.dart';
import '../theme/tokens.dart';
import '../util/format.dart';
import '../widgets/booking_ui.dart';
import '../widgets/chrome.dart';

class BookScreen extends StatefulWidget {
  const BookScreen({super.key, this.period});

  final String? period;

  @override
  State<BookScreen> createState() => _BookScreenState();
}

class _BookScreenState extends State<BookScreen> {
  int _step = 1;
  late DateTime _date;
  List<Court> _courts = const [];
  Court? _court;
  SlotGrid? _grid;
  final List<Slot> _selected = [];
  Booking? _hold;
  bool _loading = false;
  bool _paying = false;
  String? _error;
  final Map<String, int> _availability = {};

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _date = DateTime(now.year, now.month, now.day);
    if (widget.period != null) _step = 2;
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    final api = context.read<SessionController>().api;
    try {
      final courts = await api.courts();
      if (!mounted) return;
      setState(() => _courts = courts);
      await _refreshAvailability();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _refreshAvailability() async {
    final api = context.read<SessionController>().api;
    final date = formatIso(_date);
    final left = <String, int>{};
    for (final court in _courts) {
      try {
        final grid = await api.slots(date: date, courtId: court.id);
        left[court.id] = grid.availableCount;
      } catch (_) {
        left[court.id] = 0;
      }
    }
    if (!mounted) return;
    setState(() {
      _availability
        ..clear()
        ..addAll(left);
    });
  }

  Future<void> _loadSlots() async {
    if (_court == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final grid = await context.read<SessionController>().api.slots(
        date: formatIso(_date),
        courtId: _court!.id,
      );
      if (!mounted) return;
      setState(() => _grid = grid);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggleSlot(Slot slot) {
    if (!slot.isOpen) return;
    setState(() {
      final already = _selected.any((s) => s.startTime == slot.startTime);
      if (already) {
        _selected.removeWhere((s) => s.startTime == slot.startTime);
        return;
      }
      final next = [..._selected, slot];
      if (next.length <= 4 && _isConsecutive(next)) {
        _selected
          ..clear()
          ..addAll(next);
      } else {
        _selected
          ..clear()
          ..add(slot);
      }
    });
  }

  bool _isConsecutive(List<Slot> slots) {
    if (slots.isEmpty) return true;
    final hours = slots.map((s) => int.parse(s.startTime.split(':').first)).toList()
      ..sort();
    for (var i = 1; i < hours.length; i++) {
      if (hours[i] != hours[i - 1] + 1) return false;
    }
    return true;
  }

  Future<void> _holdSelected() async {
    final session = context.read<SessionController>();
    if (session.user == null) {
      context.push('/login?next=/book');
      return;
    }
    if (_selected.isEmpty || _court == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      if (_hold != null) {
        try {
          await session.api.cancelHold(
            accessToken: session.accessToken!,
            bookingId: _hold!.id,
          );
        } catch (_) {}
      }
      final times = _selected.map((s) => s.startTime).toList()..sort();
      final booking = await session.api.hold(
        accessToken: session.accessToken!,
        courtId: _court!.id,
        date: formatIso(_date),
        startTimes: times,
        attendeeNames: [session.user!.name],
      );
      if (!mounted) return;
      setState(() {
        _hold = booking;
        _step = 4;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(e.message)));
      await _loadSlots();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _cancelHold() async {
    final session = context.read<SessionController>();
    if (_hold != null && session.accessToken != null) {
      try {
        await session.api.cancelHold(
          accessToken: session.accessToken!,
          bookingId: _hold!.id,
        );
      } catch (_) {}
    }
    if (!mounted) return;
    setState(() {
      _hold = null;
      _selected.clear();
      _step = 3;
    });
    await _loadSlots();
  }

  Future<void> _pay() async {
    final session = context.read<SessionController>();
    if (_hold == null || session.accessToken == null) return;
    setState(() => _paying = true);
    try {
      final checkout = await session.api.checkout(
        accessToken: session.accessToken!,
        bookingId: _hold!.id,
      );
      if (!mounted) return;
      context.go('/book/pending?id=${_hold!.id}');
      if (!checkout.checkoutUrl.startsWith('mock://')) {
        await launchUrl(
          Uri.parse(checkout.checkoutUrl),
          mode: LaunchMode.inAppBrowserView,
        );
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(e.message)));
      if (e.code == 'HOLD_EXPIRED' || e.code == 'SLOT_TAKEN') {
        await _cancelHold();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Column(
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Book a court',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
              ),
              const SizedBox(height: 12),
              StepProgress(step: _step),
            ],
          ),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Text(
              _error!,
              style: const TextStyle(color: Color(0xFFC0392B)),
            ),
          ),
        Expanded(
          child: ScreenBody(
            child: switch (_step) {
              1 => _dateStep(),
              2 => _courtStep(),
              3 => _slotStep(),
              _ => _confirmStep(),
            },
          ),
        ),
      ],
    );
  }

  Widget _dateStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'When do you want to play?',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 6),
        Text(
          'Book up to 14 days ahead',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        DateStrip(
          selected: _date,
          onSelected: (d) async {
            setState(() => _date = d);
            await _refreshAvailability();
          },
        ),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () async {
            final picked = await showDatePicker(
              context: context,
              initialDate: _date,
              firstDate: DateTime.now(),
              lastDate: DateTime.now().add(const Duration(days: 13)),
            );
            if (picked != null) {
              setState(() => _date = picked);
              await _refreshAvailability();
            }
          },
          icon: const Icon(Icons.calendar_month_outlined),
          label: const Text('Open calendar'),
        ),
        const SizedBox(height: 28),
        PrimaryButton(
          label: 'Next',
          onPressed: () => setState(() => _step = 2),
        ),
        const SizedBox(height: 12),
      ],
    );
  }

  Widget _courtStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(formatDay(_date), style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 12),
        for (final court in _courts) ...[
          AppCard(
            onTap: () async {
              setState(() {
                _court = court;
                _selected.clear();
                _step = 3;
              });
              await _loadSlots();
            },
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: MahgouzColors.courtGreen.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.sports_tennis,
                    color: MahgouzColors.courtGreen,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        court.name,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Outdoor · 4 players',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      Text(
                        '${_availability[court.id] ?? '—'} slots available',
                        style: const TextStyle(
                          color: MahgouzColors.courtGreen,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        TextButton(
          onPressed: () => setState(() => _step = 1),
          child: const Text('← Back'),
        ),
      ],
    );
  }

  Widget _slotStep() {
    if (_grid == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final groups = <String, List<Slot>>{};
    for (final slot in _grid!.slots) {
      groups.putIfAbsent(slot.period, () => []).add(slot);
    }
    final selectedHours = _selected.length;
    final selectedTotal = _selected.fold<int>(0, (sum, slot) => sum + slot.priceEgp);
    return Column(
      children: [
        Expanded(
          child: ListView(
            children: [
              Text(
                '${_court?.name} · ${formatDay(_date)}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 6),
              Text(
                'Tap consecutive hours — up to 4.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              for (final period in ['morning', 'afternoon', 'evening'])
                if (groups[period] != null) ...[
                  Row(
                    children: [
                      Text(
                        periodLabel(period),
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const Spacer(),
                      Text(
                        formatEgp(groups[period]!.first.priceEgp),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final slot in groups[period]!)
                        SlotChip(
                          time: slot.startTime,
                          state: slot.state,
                          selected: _selected.any(
                            (s) => s.startTime == slot.startTime,
                          ),
                          onTap: slot.isOpen ? () => _toggleSlot(slot) : null,
                        ),
                    ],
                  ),
                  const SizedBox(height: 20),
                ],
              Text(
                'Legend: green open · yellow paying · grey taken',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => setState(() => _step = 2),
                child: const Text('← Courts'),
              ),
            ],
          ),
        ),
        if (_selected.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8, bottom: 12),
            child: PrimaryButton(
              label:
                  'Hold $selectedHours hr${selectedHours == 1 ? '' : 's'} · ${formatEgp(selectedTotal)}',
              loading: _loading,
              onPressed: _holdSelected,
            ),
          ),
      ],
    );
  }

  Widget _confirmStep() {
    final session = context.watch<SessionController>();
    final booking = _hold;
    if (booking == null) {
      return const Center(child: Text('Pick a slot to continue.'));
    }
    return ListView(
      children: [
        Text('Your booking', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                booking.court.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 6),
              Text(
                '${formatDay(DateTime.parse(booking.date))} · ${booking.startTime}–${booking.endTime}',
              ),
              Text(
                '${booking.durationHours} hour${booking.durationHours == 1 ? '' : 's'}',
              ),
              const Divider(height: 24),
              Row(
                children: [
                  const Text('Total'),
                  const Spacer(),
                  Text(
                    formatEgp(booking.priceEgp),
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          session.user?.name ?? '',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        Text(
          session.user?.phone ?? '',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 8),
        Text(
          '${booking.attendeeNames.length} player${booking.attendeeNames.length == 1 ? '' : 's'}',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        if (booking.holdExpiresAt != null)
          HoldTimer(expiresAt: booking.holdExpiresAt!),
        const SizedBox(height: 20),
        PrimaryButton(
          label: 'Pay with Paymob',
          loading: _paying,
          onPressed: _pay,
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: _cancelHold,
          child: const Text('Cancel releases your slot'),
        ),
      ],
    );
  }
}
