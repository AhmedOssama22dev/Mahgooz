import 'dart:convert';
import 'dart:math';

import 'package:flutter/services.dart';
import 'package:uuid/uuid.dart';

import '../config.dart';
import '../models.dart';
import '../util/format.dart';
import 'contract.dart';
import 'errors.dart';

class MockApi implements MahgoozApi {
  MockApi();

  static const _uuid = Uuid();
  static const _demoPassword = 'secret12';
  static const _staffPin = '1234';

  bool _ready = false;
  late List<Court> _courts;
  late Map<String, dynamic> _loginSeed;
  late BookingList _seedBookings;
  late Pass _seedPass;
  late StaffDay _seedStaff;
  late SlotGrid _seedSlots;
  late Pass _seedStaffPass;

  final Map<String, _MockUser> _users = {};
  final Map<String, Booking> _bookings = {};
  final Map<String, String> _slotState = {};
  final Map<String, DateTime> _checkoutAt = {};
  final List<StaffBooking> _staffExtra = [];

  Future<void> ensureLoaded() async {
    if (_ready) return;
    _courts =
        (jsonDecode(await rootBundle.loadString('assets/mock/courts.json'))
                as List)
            .map((e) => Court.fromJson(e as Map<String, dynamic>))
            .toList();
    _loginSeed =
        jsonDecode(await rootBundle.loadString('assets/mock/auth_login.json'))
            as Map<String, dynamic>;
    _seedBookings = BookingList.fromJson(
      jsonDecode(await rootBundle.loadString('assets/mock/bookings.json'))
          as Map<String, dynamic>,
    );
    _seedPass = Pass.fromJson(
      jsonDecode(await rootBundle.loadString('assets/mock/pass.json'))
          as Map<String, dynamic>,
    );
    _seedStaff = StaffDay.fromJson(
      jsonDecode(await rootBundle.loadString('assets/mock/staff_bookings.json'))
          as Map<String, dynamic>,
    );
    _seedSlots = SlotGrid.fromJson(
      jsonDecode(await rootBundle.loadString('assets/mock/slots.json'))
          as Map<String, dynamic>,
    );
    _seedStaffPass = Pass.fromJson(
      jsonDecode(await rootBundle.loadString('assets/mock/staff_pass.json'))
          as Map<String, dynamic>,
    );

    final demo = User.fromJson(_loginSeed['user'] as Map<String, dynamic>);
    _users[demo.phone] = _MockUser(user: demo, password: _demoPassword);

    for (final item in [..._seedBookings.upcoming, ..._seedBookings.past]) {
      _bookings[item.id] = Booking(
        id: item.id,
        status: item.status,
        court: Court(
          id: item.courtName == 'Court 2' ? _courts[1].id : _courts[0].id,
          name: item.courtName,
        ),
        date: item.date,
        startTime: item.startTime,
        endTime: item.endTime,
        bookerName: demo.name,
        attendeeNames: [demo.name],
        priceEgp: item.priceEgp,
        bookingCode: item.bookingCode,
        qrPayload: item.bookingCode == null
            ? null
            : 'https://mahgooz.app/pass/${item.bookingCode}',
      );
      if (item.status == 'confirmed' || item.status == 'redeemed') {
        _slotState[_key(
              item.courtName == 'Court 2' ? _courts[1].id : _courts[0].id,
              item.date,
              item.startTime,
            )] =
            'booked';
      }
    }

    for (final slot in _seedSlots.slots) {
      if (slot.state != 'available') {
        _slotState[_key(_courts.first.id, _seedSlots.date, slot.startTime)] =
            slot.state;
      }
    }

    _ready = true;
  }

  String _key(String courtId, String date, String start) =>
      '$courtId|$date|$start';

  List<String> _bookingHourStarts(Booking booking) {
    if (booking.slots.isNotEmpty) {
      return booking.slots.map((slot) => slot.startTime).toList()..sort();
    }
    final start = int.parse(booking.startTime.split(':').first);
    final end = int.parse(booking.endTime.split(':').first);
    return [
      for (var hour = start; hour < end; hour++)
        '${hour.toString().padLeft(2, '0')}:00',
    ];
  }

  void _releaseOwnUnpaidAt(String courtId, String date, String startTime) {
    Booking? match;
    for (final booking in _bookings.values) {
      if (booking.court.id != courtId || booking.date != date) continue;
      if (booking.status != 'held' && booking.status != 'pending_payment') {
        continue;
      }
      if (_bookingHourStarts(booking).contains(startTime)) {
        match = booking;
        break;
      }
    }
    if (match == null) {
      throw ApiException(
        statusCode: 409,
        code: 'SLOT_TAKEN',
        message:
            'This slot was just booked. Please choose another available slot.',
      );
    }
    for (final time in _bookingHourStarts(match)) {
      _slotState.remove(_key(match.court.id, match.date, time));
    }
    _bookings[match.id] = Booking(
      id: match.id,
      status: 'cancelled',
      court: match.court,
      date: match.date,
      startTime: match.startTime,
      endTime: match.endTime,
      bookerName: match.bookerName,
      attendeeNames: match.attendeeNames,
      priceEgp: match.priceEgp,
    );
  }

  _MockUser _requireUser(String token) {
    if (token.isEmpty) {
      throw ApiException(
        statusCode: 401,
        code: 'UNAUTHENTICATED',
        message: 'Authentication credentials were not provided.',
      );
    }
    final found = _users.values.where((u) => u.access == token);
    if (found.isEmpty) {
      // Accept any non-empty mock token from restored session.
      if (token.startsWith('mock.')) {
        return _users.values.first;
      }
      throw ApiException(
        statusCode: 401,
        code: 'UNAUTHENTICATED',
        message: 'Authentication credentials were not provided.',
      );
    }
    return found.first;
  }

  void _requireStaff(String token) {
    if (token != 'mock.staff.token' && !token.startsWith('mock.staff')) {
      throw ApiException(
        statusCode: 403,
        code: 'FORBIDDEN',
        message: 'Staff token required.',
      );
    }
  }

  @override
  Future<void> health() async {
    await ensureLoaded();
  }

  @override
  Future<List<Court>> courts() async {
    await ensureLoaded();
    return _courts;
  }

  @override
  Future<SlotGrid> slots({
    required String date,
    required String courtId,
    String? accessToken,
  }) async {
    await ensureLoaded();
    Court? court;
    for (final item in _courts) {
      if (item.id == courtId) court = item;
    }
    if (court == null) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Court not found.',
      );
    }

    final today = DateTime.now();
    final start = DateTime(today.year, today.month, today.day);
    final picked = DateTime.parse(date);
    if (picked.isBefore(start) ||
        picked.isAfter(
          start.add(const Duration(days: AppConfig.bookAheadDays)),
        )) {
      throw ApiException(
        statusCode: 400,
        code: 'DATE_OUT_OF_RANGE',
        message: 'Date must be today or within the next 14 days.',
      );
    }

    final slots = <Slot>[];
    for (var hour = 8; hour <= 21; hour++) {
      final startTime = '${hour.toString().padLeft(2, '0')}:00';
      final endTime = '${(hour + 1).toString().padLeft(2, '0')}:00';
      final period = periodForHour(hour);
      final price = priceForPeriod(period);
      var state = _slotState[_key(courtId, date, startTime)] ?? 'available';

      if (date == _seedSlots.date && courtId == _courts.first.id) {
        final seed = _seedSlots.slots.where((s) => s.startTime == startTime);
        if (seed.isNotEmpty &&
            !_slotState.containsKey(_key(courtId, date, startTime))) {
          state = seed.first.state;
        }
      }

      slots.add(
        Slot(
          startTime: startTime,
          endTime: endTime,
          state: state,
          period: period,
          priceEgp: price,
          priceCents: price * 100,
          label: period == 'morning' ? 'Morning available' : null,
          heldByMe: accessToken != null && state == 'held',
        ),
      );
    }

    return SlotGrid(date: date, court: court, slots: slots);
  }

  @override
  Future<Pass> publicPass(String code) async {
    await ensureLoaded();
    final normalized = code.toUpperCase();
    if (normalized == _seedPass.bookingCode) {
      final live = _bookings.values.where((b) => b.bookingCode == normalized);
      if (live.isNotEmpty) {
        return _passFromBooking(live.first);
      }
      return _seedPass;
    }
    final match = _bookings.values.where((b) => b.bookingCode == normalized);
    if (match.isEmpty ||
        (match.first.status != 'confirmed' &&
            match.first.status != 'redeemed')) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'No paid booking for this code.',
      );
    }
    return _passFromBooking(match.first);
  }

  Pass _passFromBooking(Booking b) => Pass(
    bookingCode: b.bookingCode!,
    status: b.status,
    court: b.court,
    date: b.date,
    startTime: b.startTime,
    endTime: b.endTime,
    bookerName: b.bookerName,
    attendeeNames: b.attendeeNames,
    priceEgp: b.priceEgp,
    qrPayload: b.qrPayload ?? 'https://mahgooz.app/pass/${b.bookingCode}',
    redeemedAt: b.redeemedAt,
  );

  @override
  Future<AuthSession> register({
    required String name,
    required String phone,
    required String password,
  }) async {
    await ensureLoaded();
    if (!isEgyptianPhone(phone)) {
      throw ApiException(
        statusCode: 400,
        code: 'VALIDATION_ERROR',
        message: 'Enter an Egyptian mobile number like 01xxxxxxxxx.',
      );
    }
    if (password.length < 6) {
      throw ApiException(
        statusCode: 400,
        code: 'VALIDATION_ERROR',
        message: 'Ensure this field has at least 6 characters.',
      );
    }
    if (_users.containsKey(phone)) {
      throw ApiException(
        statusCode: 409,
        code: 'PHONE_TAKEN',
        message: 'An account with this phone already exists.',
      );
    }
    final user = User(id: _uuid.v4(), name: name, phone: phone);
    final mock = _MockUser(user: user, password: password)
      ..access = 'mock.access.${user.id}'
      ..refresh = 'mock.refresh.${user.id}';
    _users[phone] = mock;
    return AuthSession(access: mock.access, refresh: mock.refresh, user: user);
  }

  @override
  Future<AuthSession> login({
    required String phone,
    required String password,
  }) async {
    await ensureLoaded();
    final mock = _users[phone];
    if (mock == null || mock.password != password) {
      throw ApiException(
        statusCode: 401,
        code: 'INVALID_CREDENTIALS',
        message: 'Phone or password is incorrect.',
      );
    }
    mock.access = 'mock.access.${mock.user.id}';
    mock.refresh = 'mock.refresh.${mock.user.id}';
    return AuthSession(
      access: mock.access,
      refresh: mock.refresh,
      user: mock.user,
    );
  }

  @override
  Future<String> refresh(String refreshToken) async {
    await ensureLoaded();
    return 'mock.access.refreshed';
  }

  @override
  Future<User> me(String accessToken) async {
    await ensureLoaded();
    return _requireUser(accessToken).user;
  }

  @override
  Future<Booking> hold({
    required String accessToken,
    required String courtId,
    required String date,
    required List<String> startTimes,
    required List<String> attendeeNames,
  }) async {
    await ensureLoaded();
    final user = _requireUser(accessToken);
    if (attendeeNames.isEmpty || attendeeNames.length > 4) {
      throw ApiException(
        statusCode: 400,
        code: 'VALIDATION_ERROR',
        message: 'Provide between 1 and 4 attendee names.',
      );
    }
    if (startTimes.isEmpty || startTimes.length > 4) {
      throw ApiException(
        statusCode: 400,
        code: 'VALIDATION_ERROR',
        message: 'Hold 1 to 4 consecutive hours.',
      );
    }
    final court = _courts.firstWhere(
      (c) => c.id == courtId,
      orElse: () => throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Court not found.',
      ),
    );
    final sorted = [...startTimes]..sort();
    final existing = _bookings.values.where((b) {
      if (b.court.id != courtId || b.date != date) return false;
      if (b.status != 'held' && b.status != 'pending_payment') return false;
      final times = _bookingHourStarts(b);
      return times.length == sorted.length &&
          times.every((t) => sorted.contains(t));
    }).toList();
    if (existing.isNotEmpty) {
      return existing.first;
    }
    var total = 0;
    for (final startTime in sorted) {
      final key = _key(courtId, date, startTime);
      final state = _slotState[key];
      if (state == 'booked') {
        throw ApiException(
          statusCode: 409,
          code: 'SLOT_TAKEN',
          message:
              'This slot was just booked. Please choose another available slot.',
        );
      }
      if (state == 'held') {
        _releaseOwnUnpaidAt(courtId, date, startTime);
      }
      final hour = int.parse(startTime.split(':').first);
      total += priceForPeriod(periodForHour(hour));
    }
    for (final startTime in sorted) {
      _slotState[_key(courtId, date, startTime)] = 'held';
    }
    final now = DateTime.now();
    final booking = Booking(
      id: _uuid.v4(),
      status: 'held',
      court: court,
      date: date,
      startTime: sorted.first,
      endTime: addHour(sorted.last),
      bookerName: user.user.name,
      attendeeNames: attendeeNames,
      priceEgp: total,
      priceCents: total * 100,
      holdExpiresAt: now.add(AppConfig.holdTtl),
      createdAt: now,
    );
    _bookings[booking.id] = booking;
    return booking;
  }

  @override
  Future<void> cancelHold({
    required String accessToken,
    required String bookingId,
  }) async {
    await ensureLoaded();
    _requireUser(accessToken);
    final booking = _bookings[bookingId];
    if (booking == null) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Booking not found.',
      );
    }
    if (booking.status == 'confirmed' || booking.status == 'redeemed') {
      throw ApiException(
        statusCode: 409,
        code: 'CANNOT_CANCEL',
        message: 'Paid bookings cannot be cancelled in MVP (no refunds).',
      );
    }
    _slotState.remove(_key(booking.court.id, booking.date, booking.startTime));
    _bookings[bookingId] = Booking(
      id: booking.id,
      status: 'cancelled',
      court: booking.court,
      date: booking.date,
      startTime: booking.startTime,
      endTime: booking.endTime,
      bookerName: booking.bookerName,
      attendeeNames: booking.attendeeNames,
      priceEgp: booking.priceEgp,
    );
  }

  @override
  Future<Checkout> checkout({
    required String accessToken,
    required String bookingId,
  }) async {
    await ensureLoaded();
    _requireUser(accessToken);
    final booking = _bookings[bookingId];
    if (booking == null) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Booking not found.',
      );
    }
    if (booking.status == 'confirmed') {
      throw ApiException(
        statusCode: 409,
        code: 'ALREADY_PAID',
        message: 'This booking is already confirmed.',
      );
    }
    if (booking.holdExpiresAt != null &&
        booking.holdExpiresAt!.isBefore(DateTime.now())) {
      throw ApiException(
        statusCode: 409,
        code: 'HOLD_EXPIRED',
        message: 'Your hold expired. Please pick the slot again.',
      );
    }
    _bookings[bookingId] = Booking(
      id: booking.id,
      status: 'pending_payment',
      court: booking.court,
      date: booking.date,
      startTime: booking.startTime,
      endTime: booking.endTime,
      bookerName: booking.bookerName,
      attendeeNames: booking.attendeeNames,
      priceEgp: booking.priceEgp,
      priceCents: booking.priceCents,
      holdExpiresAt: booking.holdExpiresAt,
      createdAt: booking.createdAt,
    );
    _checkoutAt[bookingId] = DateTime.now();
    return Checkout(
      bookingId: bookingId,
      status: 'pending_payment',
      amountEgp: booking.priceEgp,
      checkoutUrl: 'mock://paymob/success?booking_id=$bookingId',
    );
  }

  @override
  Future<BookingStatus> bookingStatus({
    required String accessToken,
    required String bookingId,
  }) async {
    await ensureLoaded();
    _requireUser(accessToken);
    var booking = _bookings[bookingId];
    if (booking == null) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Booking not found.',
      );
    }
    final started = _checkoutAt[bookingId];
    if (booking.status == 'pending_payment' &&
        started != null &&
        DateTime.now().difference(started) >= const Duration(seconds: 2)) {
      final code = _code();
      booking = Booking(
        id: booking.id,
        status: 'confirmed',
        court: booking.court,
        date: booking.date,
        startTime: booking.startTime,
        endTime: booking.endTime,
        bookerName: booking.bookerName,
        attendeeNames: booking.attendeeNames,
        priceEgp: booking.priceEgp,
        priceCents: booking.priceCents,
        bookingCode: code,
        qrPayload: 'https://mahgooz.app/pass/$code',
        createdAt: booking.createdAt,
        paidAt: DateTime.now(),
      );
      _bookings[bookingId] = booking;
      _slotState[_key(booking.court.id, booking.date, booking.startTime)] =
          'booked';
      _staffExtra.add(
        StaffBooking(
          bookingCode: code,
          status: 'confirmed',
          courtName: booking.court.name,
          startTime: booking.startTime,
          endTime: booking.endTime,
          bookerName: booking.bookerName,
        ),
      );
    }
    return BookingStatus(
      id: booking.id,
      status: booking.status,
      bookingCode: booking.bookingCode,
      passUrl: booking.bookingCode == null
          ? null
          : '/pass/${booking.bookingCode}',
      holdExpiresAt: booking.holdExpiresAt,
    );
  }

  String _code() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    final r = Random();
    return 'MGZ-${List.generate(5, (_) => chars[r.nextInt(chars.length)]).join()}';
  }

  @override
  Future<BookingList> myBookings(String accessToken) async {
    await ensureLoaded();
    final user = _requireUser(accessToken);
    final mine = _bookings.values
        .where(
          (b) =>
              b.bookerName == user.user.name &&
              b.status != 'cancelled' &&
              b.status != 'held',
        )
        .toList();

    final today = DateTime.now();
    final start = DateTime(today.year, today.month, today.day);
    final upcoming = <BookingSummary>[];
    final past = <BookingSummary>[];

    BookingSummary toSummary(Booking b) => BookingSummary(
      id: b.id,
      status: b.status,
      courtName: b.court.name,
      date: b.date,
      startTime: b.startTime,
      endTime: b.endTime,
      priceEgp: b.priceEgp,
      bookingCode: b.bookingCode,
      period: periodForHour(int.parse(b.startTime.split(':').first)),
    );

    if (user.user.phone == '01012345678') {
      upcoming.addAll(_seedBookings.upcoming);
      past.addAll(_seedBookings.past);
    }

    for (final b in mine) {
      final date = DateTime.parse(b.date);
      final summary = toSummary(b);
      final exists = [...upcoming, ...past].any((s) => s.id == b.id);
      if (exists) continue;
      if (b.status == 'redeemed' ||
          b.status == 'expired' ||
          b.status == 'failed' ||
          date.isBefore(start)) {
        past.insert(0, summary);
      } else {
        upcoming.insert(0, summary);
      }
    }
    return BookingList(upcoming: upcoming, past: past);
  }

  @override
  Future<Booking> bookingDetail({
    required String accessToken,
    required String bookingId,
  }) async {
    await ensureLoaded();
    _requireUser(accessToken);
    final booking = _bookings[bookingId];
    if (booking == null) {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'Booking not found.',
      );
    }
    return booking;
  }

  @override
  Future<String> staffLogin(String pin) async {
    await ensureLoaded();
    if (pin != _staffPin) {
      throw ApiException(
        statusCode: 401,
        code: 'INVALID_PIN',
        message: 'Staff PIN is incorrect.',
      );
    }
    return 'mock.staff.token';
  }

  @override
  Future<StaffDay> staffBookings({
    required String staffToken,
    required String date,
  }) async {
    await ensureLoaded();
    _requireStaff(staffToken);
    final extras = _staffExtra.where((b) {
      final match = _bookings.values.where(
        (x) => x.bookingCode == b.bookingCode,
      );
      return match.isEmpty || match.first.date == date;
    });
    final today = formatIso(DateTime.now());
    if (date == _seedStaff.date || date == today) {
      return StaffDay(
        date: date,
        bookings: [..._seedStaff.bookings, ...extras],
      );
    }
    return StaffDay(date: date, bookings: extras.toList());
  }

  @override
  Future<Pass> staffPass({
    required String staffToken,
    required String code,
  }) async {
    await ensureLoaded();
    _requireStaff(staffToken);
    final normalized = code.toUpperCase();
    if (normalized == _seedStaffPass.bookingCode) {
      final live = _bookings.values.where((b) => b.bookingCode == normalized);
      if (live.isNotEmpty && live.first.status == 'redeemed') {
        return Pass(
          bookingCode: normalized,
          status: 'redeemed',
          court: live.first.court,
          date: live.first.date,
          startTime: live.first.startTime,
          endTime: live.first.endTime,
          bookerName: live.first.bookerName,
          attendeeNames: live.first.attendeeNames,
          priceEgp: live.first.priceEgp,
          qrPayload: live.first.qrPayload ?? '',
          redeemedAt: live.first.redeemedAt,
          bookerPhone: '01012345678',
          canRedeem: false,
        );
      }
      return _seedStaffPass;
    }
    try {
      final pass = await publicPass(normalized);
      return Pass(
        bookingCode: pass.bookingCode,
        status: pass.status,
        court: pass.court,
        date: pass.date,
        startTime: pass.startTime,
        endTime: pass.endTime,
        bookerName: pass.bookerName,
        attendeeNames: pass.attendeeNames,
        priceEgp: pass.priceEgp,
        qrPayload: pass.qrPayload,
        redeemedAt: pass.redeemedAt,
        bookerPhone: '01012345678',
        canRedeem: pass.status == 'confirmed',
      );
    } on ApiException {
      throw ApiException(
        statusCode: 404,
        code: 'NOT_FOUND',
        message: 'No booking for this code.',
      );
    }
  }

  @override
  Future<Pass> redeem({
    required String staffToken,
    required String code,
  }) async {
    await ensureLoaded();
    _requireStaff(staffToken);
    final pass = await staffPass(staffToken: staffToken, code: code);
    if (pass.status == 'redeemed') {
      throw ApiException(
        statusCode: 409,
        code: 'ALREADY_REDEEMED',
        message: 'This pass was already redeemed.',
      );
    }
    final now = DateTime.now();
    final match = _bookings.values.where(
      (b) => b.bookingCode == pass.bookingCode,
    );
    if (match.isNotEmpty) {
      final b = match.first;
      _bookings[b.id] = Booking(
        id: b.id,
        status: 'redeemed',
        court: b.court,
        date: b.date,
        startTime: b.startTime,
        endTime: b.endTime,
        bookerName: b.bookerName,
        attendeeNames: b.attendeeNames,
        priceEgp: b.priceEgp,
        bookingCode: b.bookingCode,
        qrPayload: b.qrPayload,
        redeemedAt: now,
      );
    }
    return Pass(
      bookingCode: pass.bookingCode,
      status: 'redeemed',
      court: pass.court,
      date: pass.date,
      startTime: pass.startTime,
      endTime: pass.endTime,
      bookerName: pass.bookerName,
      attendeeNames: pass.attendeeNames,
      priceEgp: pass.priceEgp,
      qrPayload: pass.qrPayload,
      redeemedAt: now,
      bookerPhone: pass.bookerPhone,
      canRedeem: false,
    );
  }
}

class _MockUser {
  _MockUser({required this.user, required this.password});

  final User user;
  final String password;
  String access = 'mock.access.token';
  String refresh = 'mock.refresh.token';
}
