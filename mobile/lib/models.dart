class User {
  const User({required this.id, required this.name, required this.phone});

  final String id;
  final String name;
  final String phone;

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'] as String,
    name: json['name'] as String,
    phone: json['phone'] as String,
  );

  Map<String, dynamic> toJson() => {'id': id, 'name': name, 'phone': phone};
}

class AuthSession {
  const AuthSession({required this.access, this.refresh, required this.user});

  final String access;
  final String? refresh;
  final User user;

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
    access: json['access'] as String,
    refresh: json['refresh'] as String?,
    user: User.fromJson(json['user'] as Map<String, dynamic>),
  );
}

class Court {
  const Court({required this.id, required this.name, this.slug});

  final String id;
  final String name;
  final String? slug;

  factory Court.fromJson(Map<String, dynamic> json) => Court(
    id: json['id'] as String,
    name: json['name'] as String,
    slug: json['slug'] as String?,
  );
}

class Slot {
  const Slot({
    required this.startTime,
    required this.endTime,
    required this.state,
    required this.period,
    required this.priceEgp,
    required this.priceCents,
    this.label,
  });

  final String startTime;
  final String endTime;
  final String state;
  final String period;
  final int priceEgp;
  final int priceCents;
  final String? label;

  bool get isOpen => state == 'available';

  factory Slot.fromJson(Map<String, dynamic> json) => Slot(
    startTime: json['start_time'] as String,
    endTime: json['end_time'] as String,
    state: json['state'] as String,
    period: json['period'] as String,
    priceEgp: json['price_egp'] as int,
    priceCents: json['price_cents'] as int,
    label: json['label'] as String?,
  );

  Slot copyWith({String? state}) => Slot(
    startTime: startTime,
    endTime: endTime,
    state: state ?? this.state,
    period: period,
    priceEgp: priceEgp,
    priceCents: priceCents,
    label: label,
  );
}

class SlotGrid {
  const SlotGrid({
    required this.date,
    required this.court,
    required this.slots,
  });

  final String date;
  final Court court;
  final List<Slot> slots;

  int get availableCount => slots.where((s) => s.isOpen).length;

  factory SlotGrid.fromJson(Map<String, dynamic> json) => SlotGrid(
    date: json['date'] as String,
    court: Court.fromJson(json['court'] as Map<String, dynamic>),
    slots: (json['slots'] as List)
        .map((e) => Slot.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class BookingSummary {
  const BookingSummary({
    required this.id,
    required this.status,
    required this.courtName,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.priceEgp,
    this.bookingCode,
    this.period,
  });

  final String id;
  final String status;
  final String courtName;
  final String date;
  final String startTime;
  final String endTime;
  final int priceEgp;
  final String? bookingCode;
  final String? period;

  factory BookingSummary.fromJson(Map<String, dynamic> json) => BookingSummary(
    id: json['id'] as String,
    status: json['status'] as String,
    courtName: json['court_name'] as String,
    date: json['date'] as String,
    startTime: json['start_time'] as String,
    endTime: json['end_time'] as String,
    priceEgp: json['price_egp'] as int,
    bookingCode: json['booking_code'] as String?,
    period: json['period'] as String?,
  );
}

class BookingList {
  const BookingList({required this.upcoming, required this.past});

  final List<BookingSummary> upcoming;
  final List<BookingSummary> past;

  factory BookingList.fromJson(Map<String, dynamic> json) => BookingList(
    upcoming: (json['upcoming'] as List)
        .map((e) => BookingSummary.fromJson(e as Map<String, dynamic>))
        .toList(),
    past: (json['past'] as List)
        .map((e) => BookingSummary.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class Booking {
  const Booking({
    required this.id,
    required this.status,
    required this.court,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.bookerName,
    required this.attendeeNames,
    required this.priceEgp,
    this.priceCents,
    this.holdExpiresAt,
    this.bookingCode,
    this.qrPayload,
    this.redeemedAt,
    this.createdAt,
    this.paidAt,
  });

  final String id;
  final String status;
  final Court court;
  final String date;
  final String startTime;
  final String endTime;
  final String bookerName;
  final List<String> attendeeNames;
  final int priceEgp;
  final int? priceCents;
  final DateTime? holdExpiresAt;
  final String? bookingCode;
  final String? qrPayload;
  final DateTime? redeemedAt;
  final DateTime? createdAt;
  final DateTime? paidAt;

  factory Booking.fromJson(Map<String, dynamic> json) {
    final courtJson = json['court'];
    return Booking(
      id: json['id'] as String,
      status: json['status'] as String,
      court: courtJson is Map<String, dynamic>
          ? Court.fromJson(courtJson)
          : Court(id: '', name: json['court_name'] as String? ?? 'Court'),
      date: json['date'] as String,
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
      bookerName: json['booker_name'] as String? ?? '',
      attendeeNames:
          (json['attendee_names'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      priceEgp: json['price_egp'] as int,
      priceCents: json['price_cents'] as int?,
      holdExpiresAt: json['hold_expires_at'] != null
          ? DateTime.parse(json['hold_expires_at'] as String)
          : null,
      bookingCode: json['booking_code'] as String?,
      qrPayload: json['qr_payload'] as String?,
      redeemedAt: json['redeemed_at'] != null
          ? DateTime.parse(json['redeemed_at'] as String)
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
      paidAt: json['paid_at'] != null
          ? DateTime.parse(json['paid_at'] as String)
          : null,
    );
  }
}

class BookingStatus {
  const BookingStatus({
    required this.id,
    required this.status,
    this.bookingCode,
    this.passUrl,
    this.holdExpiresAt,
  });

  final String id;
  final String status;
  final String? bookingCode;
  final String? passUrl;
  final DateTime? holdExpiresAt;

  factory BookingStatus.fromJson(Map<String, dynamic> json) => BookingStatus(
    id: json['id'] as String,
    status: json['status'] as String,
    bookingCode: json['booking_code'] as String?,
    passUrl: json['pass_url'] as String?,
    holdExpiresAt: json['hold_expires_at'] != null
        ? DateTime.parse(json['hold_expires_at'] as String)
        : null,
  );
}

class Checkout {
  const Checkout({
    required this.bookingId,
    required this.status,
    required this.amountEgp,
    required this.checkoutUrl,
  });

  final String bookingId;
  final String status;
  final int amountEgp;
  final String checkoutUrl;

  factory Checkout.fromJson(Map<String, dynamic> json) => Checkout(
    bookingId: json['booking_id'] as String,
    status: json['status'] as String,
    amountEgp: json['amount_egp'] as int,
    checkoutUrl: json['checkout_url'] as String,
  );
}

class Pass {
  const Pass({
    required this.bookingCode,
    required this.status,
    required this.court,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.bookerName,
    required this.attendeeNames,
    required this.priceEgp,
    required this.qrPayload,
    this.redeemedAt,
    this.bookerPhone,
    this.canRedeem,
    this.paymobTransactionId,
  });

  final String bookingCode;
  final String status;
  final Court court;
  final String date;
  final String startTime;
  final String endTime;
  final String bookerName;
  final List<String> attendeeNames;
  final int priceEgp;
  final String qrPayload;
  final DateTime? redeemedAt;
  final String? bookerPhone;
  final bool? canRedeem;
  final int? paymobTransactionId;

  factory Pass.fromJson(Map<String, dynamic> json) => Pass(
    bookingCode: json['booking_code'] as String,
    status: json['status'] as String,
    court: Court.fromJson(json['court'] as Map<String, dynamic>),
    date: json['date'] as String,
    startTime: json['start_time'] as String,
    endTime: json['end_time'] as String,
    bookerName: json['booker_name'] as String,
    attendeeNames: (json['attendee_names'] as List)
        .map((e) => e.toString())
        .toList(),
    priceEgp: json['price_egp'] as int,
    qrPayload:
        json['qr_payload'] as String? ??
        'https://mahgooz.app/pass/${json['booking_code']}',
    redeemedAt: json['redeemed_at'] != null
        ? DateTime.parse(json['redeemed_at'] as String)
        : null,
    bookerPhone: json['booker_phone'] as String?,
    canRedeem: json['can_redeem'] as bool?,
    paymobTransactionId: json['paymob_transaction_id'] as int?,
  );
}

class StaffBooking {
  const StaffBooking({
    required this.bookingCode,
    required this.status,
    required this.courtName,
    required this.startTime,
    required this.endTime,
    required this.bookerName,
    this.bookerPhone,
    this.redeemedAt,
  });

  final String bookingCode;
  final String status;
  final String courtName;
  final String startTime;
  final String endTime;
  final String bookerName;
  final String? bookerPhone;
  final DateTime? redeemedAt;

  factory StaffBooking.fromJson(Map<String, dynamic> json) => StaffBooking(
    bookingCode: json['booking_code'] as String,
    status: json['status'] as String,
    courtName: json['court_name'] as String,
    startTime: json['start_time'] as String,
    endTime: json['end_time'] as String,
    bookerName: json['booker_name'] as String,
    bookerPhone: json['booker_phone'] as String?,
    redeemedAt: json['redeemed_at'] != null
        ? DateTime.parse(json['redeemed_at'] as String)
        : null,
  );
}

class StaffDay {
  const StaffDay({required this.date, required this.bookings});

  final String date;
  final List<StaffBooking> bookings;

  factory StaffDay.fromJson(Map<String, dynamic> json) => StaffDay(
    date: json['date'] as String,
    bookings: (json['bookings'] as List)
        .map((e) => StaffBooking.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}
