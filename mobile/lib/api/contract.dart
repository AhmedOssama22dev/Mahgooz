import '../models.dart';

abstract class MahgoozApi {
  Future<void> health();

  Future<List<Court>> courts();

  Future<SlotGrid> slots({required String date, required String courtId});

  Future<Pass> publicPass(String code);

  Future<AuthSession> register({
    required String name,
    required String phone,
    required String password,
  });

  Future<AuthSession> login({required String phone, required String password});

  Future<String> refresh(String refreshToken);

  Future<User> me(String accessToken);

  Future<Booking> hold({
    required String accessToken,
    required String courtId,
    required String date,
    required String startTime,
    required List<String> attendeeNames,
  });

  Future<void> cancelHold({
    required String accessToken,
    required String bookingId,
  });

  Future<Checkout> checkout({
    required String accessToken,
    required String bookingId,
  });

  Future<BookingStatus> bookingStatus({
    required String accessToken,
    required String bookingId,
  });

  Future<BookingList> myBookings(String accessToken);

  Future<Booking> bookingDetail({
    required String accessToken,
    required String bookingId,
  });

  Future<String> staffLogin(String pin);

  Future<StaffDay> staffBookings({
    required String staffToken,
    required String date,
  });

  Future<Pass> staffPass({required String staffToken, required String code});

  Future<Pass> redeem({required String staffToken, required String code});
}
