import 'package:intl/intl.dart';

final _day = DateFormat('EEE d MMM');
final _dayLong = DateFormat('EEE d MMM yyyy');
final _iso = DateFormat('yyyy-MM-dd');

String formatEgp(num amount) => 'EGP ${amount.round()}';

String formatDay(DateTime date) => _day.format(date);

String formatDayLong(DateTime date) => _dayLong.format(date);

String formatIso(DateTime date) => _iso.format(date);

DateTime parseIsoDate(String value) => DateTime.parse(value);

String formatSlotRange(String start, String end) => '$start–$end';

String addHour(String hhmm) {
  final parts = hhmm.split(':');
  final h = int.parse(parts[0]) + 1;
  return '${h.toString().padLeft(2, '0')}:${parts[1]}';
}

String periodLabel(String period) {
  switch (period) {
    case 'morning':
      return 'Morning';
    case 'afternoon':
      return 'Afternoon';
    case 'evening':
      return 'Evening';
    default:
      return period;
  }
}

String periodForHour(int hour) {
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  return 'evening';
}

int priceForPeriod(String period) {
  switch (period) {
    case 'morning':
      return 200;
    case 'afternoon':
      return 280;
    default:
      return 350;
  }
}

String remainingHold(DateTime expiresAt) {
  final left = expiresAt.difference(DateTime.now());
  if (left.isNegative) return '0:00';
  final m = left.inMinutes;
  final s = left.inSeconds % 60;
  return '$m:${s.toString().padLeft(2, '0')}';
}

bool isEgyptianPhone(String phone) => RegExp(r'^01\d{9}$').hasMatch(phone);
