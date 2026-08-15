import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import '../util/format.dart';

class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.status, this.period});

  final String status;
  final String? period;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    late String label;
    late Color bg;
    late Color fg;

    switch (status) {
      case 'confirmed':
      case 'paid':
        label = 'Ready to play';
        bg = dark
            ? MahgouzColors.slotAvailableDark
            : MahgouzColors.courtGreenLight;
        fg = dark ? MahgouzColors.courtGreen : MahgouzColors.courtGreenDark;
      case 'pending_payment':
      case 'held':
        label = 'Confirming…';
        bg = dark ? MahgouzColors.slotHeldDark : MahgouzColors.slotHeldLight;
        fg = dark
            ? MahgouzColors.slotHeldTextDark
            : MahgouzColors.slotHeldTextLight;
      case 'redeemed':
        label = 'Checked in';
        bg = dark
            ? MahgouzColors.slotBookedDark
            : MahgouzColors.slotBookedLight;
        fg = MahgouzColors.redeemed;
      case 'expired':
        label = 'Past';
        bg = dark
            ? MahgouzColors.slotBookedDark
            : MahgouzColors.slotBookedLight;
        fg = Theme.of(context).colorScheme.onSurfaceVariant;
      case 'failed':
      case 'cancelled':
        label = 'Cancelled';
        bg = MahgouzColors.error.withValues(alpha: 0.12);
        fg = MahgouzColors.error;
      default:
        label = status;
        bg = dark ? MahgouzColors.darkElevated : MahgouzColors.lightBorder;
        fg = Theme.of(context).colorScheme.onSurface;
    }

    if (period == 'morning' && (status == 'confirmed' || status == 'paid')) {
      label = 'Morning deal';
      bg = dark ? MahgouzColors.promoDark : MahgouzColors.clayOrangeLight;
      fg = MahgouzColors.clayOrange;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(MahgouzRadii.full),
      ),
      child: Text(
        label,
        style: Theme.of(
          context,
        ).textTheme.labelMedium?.copyWith(color: fg, fontSize: 12),
      ),
    );
  }
}

class PromoBanner extends StatelessWidget {
  const PromoBanner({super.key, this.onTap});

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Material(
      color: dark ? MahgouzColors.promoDark : MahgouzColors.clayOrangeLight,
      borderRadius: BorderRadius.circular(MahgouzRadii.md),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(MahgouzRadii.md),
        child: Padding(
          padding: const EdgeInsets.all(MahgouzSpace.md),
          child: Row(
            children: [
              const Icon(
                Icons.wb_sunny_outlined,
                color: MahgouzColors.clayOrange,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Quiet mornings, lower price',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Before 12 PM — 30% off',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: MahgouzColors.clayOrange,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                decoration: BoxDecoration(
                  color: MahgouzColors.clayOrange,
                  borderRadius: BorderRadius.circular(MahgouzRadii.sm),
                ),
                child: const Text(
                  '30% OFF',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class StepProgress extends StatelessWidget {
  const StepProgress({super.key, required this.step});

  final int step;

  @override
  Widget build(BuildContext context) {
    const labels = ['Date', 'Court', 'Time', 'Confirm'];
    return Row(
      children: [
        for (var i = 0; i < labels.length; i++) ...[
          if (i > 0)
            Expanded(
              child: Container(
                height: 2,
                color: i < step
                    ? MahgouzColors.courtGreen
                    : Theme.of(context).dividerColor,
              ),
            ),
          Column(
            children: [
              CircleAvatar(
                radius: 11,
                backgroundColor: i < step
                    ? MahgouzColors.courtGreen
                    : Theme.of(context).dividerColor,
                child: i < step
                    ? const Icon(Icons.check, size: 12, color: Colors.white)
                    : Text(
                        '${i + 1}',
                        style: TextStyle(
                          fontSize: 10,
                          color: Theme.of(context).colorScheme.onSurface,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
              ),
              const SizedBox(height: 4),
              Text(labels[i], style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ],
      ],
    );
  }
}

class DateStrip extends StatelessWidget {
  const DateStrip({
    super.key,
    required this.selected,
    required this.onSelected,
  });

  final DateTime selected;
  final ValueChanged<DateTime> onSelected;

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now();
    final start = DateTime(today.year, today.month, today.day);
    return SizedBox(
      height: 78,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: 14,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final day = start.add(Duration(days: i));
          final active = formatIso(day) == formatIso(selected);
          return InkWell(
            onTap: () => onSelected(day),
            borderRadius: BorderRadius.circular(MahgouzRadii.md),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 64,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: active
                    ? MahgouzColors.courtGreen
                    : Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(MahgouzRadii.md),
                border: Border.all(
                  color: active
                      ? MahgouzColors.courtGreen
                      : Theme.of(context).dividerColor,
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    [
                      'Mon',
                      'Tue',
                      'Wed',
                      'Thu',
                      'Fri',
                      'Sat',
                      'Sun',
                    ][day.weekday - 1],
                    style: TextStyle(
                      fontSize: 12,
                      color: active
                          ? Colors.white
                          : Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${day.day}',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 18,
                      color: active
                          ? Colors.white
                          : Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class SlotChip extends StatelessWidget {
  const SlotChip({
    super.key,
    required this.time,
    required this.state,
    required this.selected,
    required this.onTap,
  });

  final String time;
  final String state;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    Color bg;
    Color fg;
    Color border;

    if (selected) {
      bg = MahgouzColors.courtGreen;
      fg = Colors.white;
      border = MahgouzColors.courtGreen;
    } else {
      switch (state) {
        case 'available':
          bg = dark
              ? MahgouzColors.slotAvailableDark
              : MahgouzColors.slotAvailableLight;
          fg = Theme.of(context).colorScheme.onSurface;
          border = MahgouzColors.courtGreen;
        case 'held':
          bg = dark ? MahgouzColors.slotHeldDark : MahgouzColors.slotHeldLight;
          fg = dark
              ? MahgouzColors.slotHeldTextDark
              : MahgouzColors.slotHeldTextLight;
          border = Colors.transparent;
        default:
          bg = dark
              ? MahgouzColors.slotBookedDark
              : MahgouzColors.slotBookedLight;
          fg = Theme.of(context).colorScheme.onSurfaceVariant;
          border = Colors.transparent;
      }
    }

    final enabled = state == 'available' || selected;
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 72, minHeight: 44),
      child: Material(
        color: bg,
        borderRadius: BorderRadius.circular(MahgouzRadii.sm),
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(MahgouzRadii.sm),
          child: Container(
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(MahgouzRadii.sm),
              border: Border.all(color: border),
            ),
            child: Text(
              time,
              style: TextStyle(fontWeight: FontWeight.w600, color: fg),
            ),
          ),
        ),
      ),
    );
  }
}

class HoldTimer extends StatelessWidget {
  const HoldTimer({super.key, required this.expiresAt});

  final DateTime expiresAt;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder(
      stream: Stream.periodic(const Duration(seconds: 1)),
      builder: (context, _) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: Theme.of(context).brightness == Brightness.dark
                ? MahgouzColors.slotHeldDark
                : MahgouzColors.slotHeldLight,
            borderRadius: BorderRadius.circular(MahgouzRadii.sm),
          ),
          child: Row(
            children: [
              const Icon(
                Icons.timer_outlined,
                size: 18,
                color: MahgouzColors.clayOrange,
              ),
              const SizedBox(width: 8),
              Text(
                'Slot held · ${remainingHold(expiresAt)} left',
                style: Theme.of(context).textTheme.labelMedium,
              ),
            ],
          ),
        );
      },
    );
  }
}
