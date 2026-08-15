import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../models.dart';
import 'contract.dart';
import 'errors.dart';

class HttpApi implements MahgoozApi {
  HttpApi({http.Client? client, String? baseUrl})
    : _client = client ?? http.Client(),
      _base = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _base;

  Uri _uri(String path, [Map<String, String>? query]) =>
      Uri.parse('$_base$path').replace(queryParameters: query);

  Map<String, String> _headers([String? token]) => {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  Future<dynamic> _send(
    String method,
    String path, {
    String? token,
    Map<String, String>? query,
    Object? body,
    int successMin = 200,
    int successMax = 299,
  }) async {
    final uri = _uri(path, query);
    try {
      final request = http.Request(method, uri)
        ..headers.addAll(_headers(token));
      if (body != null) request.body = jsonEncode(body);
      final streamed = await _client
          .send(request)
          .timeout(AppConfig.requestTimeout);
      final response = await http.Response.fromStream(streamed);
      final decoded = response.body.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(response.body);
      if (response.statusCode < successMin ||
          response.statusCode > successMax) {
        if (decoded is Map<String, dynamic>) {
          throw ApiException.fromBody(response.statusCode, decoded);
        }
        throw ApiException(
          statusCode: response.statusCode,
          code: 'HTTP_${response.statusCode}',
          message: 'Request failed (${response.statusCode}).',
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw NetworkException();
    } on http.ClientException {
      throw NetworkException();
    } catch (error) {
      if (error is ApiException) rethrow;
      throw NetworkException();
    }
  }

  @override
  Future<void> health() async {
    await _send('GET', '/health');
  }

  @override
  Future<List<Court>> courts() async {
    final data = await _send('GET', '/courts');
    return (data as List)
        .map((e) => Court.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<SlotGrid> slots({
    required String date,
    required String courtId,
  }) async {
    final data = await _send(
      'GET',
      '/slots',
      query: {'date': date, 'court_id': courtId},
    );
    return SlotGrid.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<Pass> publicPass(String code) async {
    final data = await _send('GET', '/passes/$code');
    return Pass.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<AuthSession> register({
    required String name,
    required String phone,
    required String password,
  }) async {
    final data = await _send(
      'POST',
      '/auth/register',
      body: {'name': name, 'phone': phone, 'password': password},
      successMin: 200,
      successMax: 201,
    );
    return AuthSession.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<AuthSession> login({
    required String phone,
    required String password,
  }) async {
    final data = await _send(
      'POST',
      '/auth/login',
      body: {'phone': phone, 'password': password},
    );
    return AuthSession.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<String> refresh(String refreshToken) async {
    final data = await _send(
      'POST',
      '/auth/refresh',
      body: {'refresh': refreshToken},
    );
    return (data as Map<String, dynamic>)['access'] as String;
  }

  @override
  Future<User> me(String accessToken) async {
    final data = await _send('GET', '/auth/me', token: accessToken);
    return User.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<Booking> hold({
    required String accessToken,
    required String courtId,
    required String date,
    required String startTime,
    required List<String> attendeeNames,
  }) async {
    final data = await _send(
      'POST',
      '/bookings/hold',
      token: accessToken,
      body: {
        'court_id': courtId,
        'date': date,
        'start_time': startTime,
        'attendee_names': attendeeNames,
      },
      successMin: 200,
      successMax: 201,
    );
    return Booking.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<void> cancelHold({
    required String accessToken,
    required String bookingId,
  }) async {
    await _send('DELETE', '/bookings/$bookingId', token: accessToken);
  }

  @override
  Future<Checkout> checkout({
    required String accessToken,
    required String bookingId,
  }) async {
    final data = await _send(
      'POST',
      '/bookings/$bookingId/checkout',
      token: accessToken,
      body: const {},
    );
    return Checkout.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<BookingStatus> bookingStatus({
    required String accessToken,
    required String bookingId,
  }) async {
    final data = await _send(
      'GET',
      '/bookings/$bookingId/status',
      token: accessToken,
    );
    return BookingStatus.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<BookingList> myBookings(String accessToken) async {
    final data = await _send('GET', '/bookings', token: accessToken);
    return BookingList.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<Booking> bookingDetail({
    required String accessToken,
    required String bookingId,
  }) async {
    final data = await _send('GET', '/bookings/$bookingId', token: accessToken);
    return Booking.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<String> staffLogin(String pin) async {
    final data = await _send('POST', '/staff/login', body: {'pin': pin});
    return (data as Map<String, dynamic>)['access'] as String;
  }

  @override
  Future<StaffDay> staffBookings({
    required String staffToken,
    required String date,
  }) async {
    final data = await _send(
      'GET',
      '/staff/bookings',
      token: staffToken,
      query: {'date': date},
    );
    return StaffDay.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<Pass> staffPass({
    required String staffToken,
    required String code,
  }) async {
    final data = await _send('GET', '/staff/passes/$code', token: staffToken);
    return Pass.fromJson(data as Map<String, dynamic>);
  }

  @override
  Future<Pass> redeem({
    required String staffToken,
    required String code,
  }) async {
    final data = await _send(
      'POST',
      '/staff/passes/$code/redeem',
      token: staffToken,
      body: const {},
    );
    return Pass.fromJson(data as Map<String, dynamic>);
  }
}
