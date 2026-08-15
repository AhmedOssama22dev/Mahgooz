import '../models.dart';
import 'contract.dart';
import 'errors.dart';
import 'http_api.dart';
import 'mock_api.dart';

/// Tries the live Django API first. On connection failure, falls back to
/// bundled mock JSON for the rest of the session so the app stays usable.
class MahgoozRepository implements MahgoozApi {
  MahgoozRepository({HttpApi? live, MockApi? mock})
    : _live = live ?? HttpApi(),
      _mock = mock ?? MockApi();

  final HttpApi _live;
  final MockApi _mock;

  bool usingMock = false;
  void Function(bool usingMock)? onSourceChanged;

  Future<T> _guard<T>(
    Future<T> Function() live,
    Future<T> Function() mock,
  ) async {
    if (usingMock) return mock();
    try {
      return await live();
    } on NetworkException {
      usingMock = true;
      onSourceChanged?.call(true);
      await _mock.ensureLoaded();
      return mock();
    }
  }

  Future<void> probe() async {
    await _guard(() => _live.health(), () => _mock.health());
  }

  @override
  Future<void> health() => _guard(() => _live.health(), () => _mock.health());

  @override
  Future<List<Court>> courts() =>
      _guard(() => _live.courts(), () => _mock.courts());

  @override
  Future<SlotGrid> slots({required String date, required String courtId}) =>
      _guard(
        () => _live.slots(date: date, courtId: courtId),
        () => _mock.slots(date: date, courtId: courtId),
      );

  @override
  Future<Pass> publicPass(String code) =>
      _guard(() => _live.publicPass(code), () => _mock.publicPass(code));

  @override
  Future<AuthSession> register({
    required String name,
    required String phone,
    required String password,
  }) => _guard(
    () => _live.register(name: name, phone: phone, password: password),
    () => _mock.register(name: name, phone: phone, password: password),
  );

  @override
  Future<AuthSession> login({
    required String phone,
    required String password,
  }) => _guard(
    () => _live.login(phone: phone, password: password),
    () => _mock.login(phone: phone, password: password),
  );

  @override
  Future<String> refresh(String refreshToken) => _guard(
    () => _live.refresh(refreshToken),
    () => _mock.refresh(refreshToken),
  );

  @override
  Future<User> me(String accessToken) =>
      _guard(() => _live.me(accessToken), () => _mock.me(accessToken));

  @override
  Future<Booking> hold({
    required String accessToken,
    required String courtId,
    required String date,
    required List<String> startTimes,
    required List<String> attendeeNames,
  }) => _guard(
    () => _live.hold(
      accessToken: accessToken,
      courtId: courtId,
      date: date,
      startTimes: startTimes,
      attendeeNames: attendeeNames,
    ),
    () => _mock.hold(
      accessToken: accessToken,
      courtId: courtId,
      date: date,
      startTimes: startTimes,
      attendeeNames: attendeeNames,
    ),
  );

  @override
  Future<void> cancelHold({
    required String accessToken,
    required String bookingId,
  }) => _guard(
    () => _live.cancelHold(accessToken: accessToken, bookingId: bookingId),
    () => _mock.cancelHold(accessToken: accessToken, bookingId: bookingId),
  );

  @override
  Future<Checkout> checkout({
    required String accessToken,
    required String bookingId,
  }) => _guard(
    () => _live.checkout(accessToken: accessToken, bookingId: bookingId),
    () => _mock.checkout(accessToken: accessToken, bookingId: bookingId),
  );

  @override
  Future<BookingStatus> bookingStatus({
    required String accessToken,
    required String bookingId,
  }) => _guard(
    () => _live.bookingStatus(accessToken: accessToken, bookingId: bookingId),
    () => _mock.bookingStatus(accessToken: accessToken, bookingId: bookingId),
  );

  @override
  Future<BookingList> myBookings(String accessToken) => _guard(
    () => _live.myBookings(accessToken),
    () => _mock.myBookings(accessToken),
  );

  @override
  Future<Booking> bookingDetail({
    required String accessToken,
    required String bookingId,
  }) => _guard(
    () => _live.bookingDetail(accessToken: accessToken, bookingId: bookingId),
    () => _mock.bookingDetail(accessToken: accessToken, bookingId: bookingId),
  );

  @override
  Future<String> staffLogin(String pin) =>
      _guard(() => _live.staffLogin(pin), () => _mock.staffLogin(pin));

  @override
  Future<StaffDay> staffBookings({
    required String staffToken,
    required String date,
  }) => _guard(
    () => _live.staffBookings(staffToken: staffToken, date: date),
    () => _mock.staffBookings(staffToken: staffToken, date: date),
  );

  @override
  Future<Pass> staffPass({required String staffToken, required String code}) =>
      _guard(
        () => _live.staffPass(staffToken: staffToken, code: code),
        () => _mock.staffPass(staffToken: staffToken, code: code),
      );

  @override
  Future<Pass> redeem({required String staffToken, required String code}) =>
      _guard(
        () => _live.redeem(staffToken: staffToken, code: code),
        () => _mock.redeem(staffToken: staffToken, code: code),
      );
}
