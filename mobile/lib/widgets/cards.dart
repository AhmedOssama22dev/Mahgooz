import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:go_router/go_router.dart';

import '../models.dart';
import '../theme/tokens.dart';
import '../util/format.dart';
import 'booking_ui.dart';
import 'chrome.dart';

class BookingCard extends StatelessWidget {
  const BookingCard({super.key, required this.booking, this.past = false});

  final BookingSummary booking;
  final bool past;

  @override
  Widget build(BuildContext context) {
    final canViewPass =
        booking.bookingCode != null &&
        (booking.status == 'confirmed' ||
            booking.status == 'redeemed' ||
            booking.status == 'expired');

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${formatDay(DateTime.parse(booking.date))} · ${booking.startTime}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              StatusBadge(status: booking.status, period: booking.period),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '${booking.courtName} · ${formatEgp(booking.priceEgp)}',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          if (canViewPass) ...[
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => context.push('/pass/${booking.bookingCode}'),
                child: Text(past ? 'View' : 'View pass →'),
              ),
            ),
          ] else if (booking.status == 'failed' ||
              booking.status == 'cancelled') ...[
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => context.go('/book'),
                child: const Text('Book again'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class PinPad extends StatelessWidget {
  const PinPad({
    super.key,
    required this.value,
    required this.onChanged,
    required this.onSubmit,
    this.error = false,
  });

  final String value;
  final ValueChanged<String> onChanged;
  final VoidCallback onSubmit;
  final bool error;

  @override
  Widget build(BuildContext context) {
    void press(String digit) {
      HapticFeedback.selectionClick();
      if (value.length >= 4) return;
      final next = value + digit;
      onChanged(next);
      if (next.length == 4) onSubmit();
    }

    void back() {
      if (value.isEmpty) return;
      onChanged(value.substring(0, value.length - 1));
    }

    Widget key(String label, {VoidCallback? onTap, IconData? icon}) {
      return SizedBox(
        width: 76,
        height: 76,
        child: Material(
          color: Theme.of(context).cardColor,
          shape: const CircleBorder(),
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: onTap,
            child: Center(
              child: icon != null
                  ? Icon(icon, color: Theme.of(context).colorScheme.onSurface)
                  : Text(
                      label,
                      style: GoogleFonts.dmSans(
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
            ),
          ),
        ),
      );
    }

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(4, (i) {
            final filled = i < value.length;
            return AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              margin: const EdgeInsets.symmetric(horizontal: 8),
              width: 16,
              height: 16,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: filled
                    ? (error ? MahgouzColors.error : MahgouzColors.courtGreen)
                    : Colors.transparent,
                border: Border.all(
                  color: error
                      ? MahgouzColors.error
                      : Theme.of(context).dividerColor,
                  width: 2,
                ),
              ),
            );
          }),
        ),
        const SizedBox(height: 28),
        Wrap(
          spacing: 18,
          runSpacing: 18,
          alignment: WrapAlignment.center,
          children: [
            for (final d in ['1', '2', '3', '4', '5', '6', '7', '8', '9'])
              key(d, onTap: () => press(d)),
            key('', onTap: back, icon: Icons.backspace_outlined),
            key('0', onTap: () => press('0')),
            key('', onTap: onSubmit, icon: Icons.check_rounded),
          ],
        ),
      ],
    );
  }
}
