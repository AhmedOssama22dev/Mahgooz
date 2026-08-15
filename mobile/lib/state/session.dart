import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/repository.dart';
import '../models.dart';

class SessionController extends ChangeNotifier {
  SessionController({MahgoozRepository? repository})
    : api = repository ?? MahgoozRepository() {
    api.onSourceChanged = (_) => notifyListeners();
  }

  final MahgoozRepository api;

  User? user;
  String? accessToken;
  String? refreshToken;
  String? staffToken;
  ThemeMode themeMode = ThemeMode.system;
  bool ready = false;
  final Completer<void> _ready = Completer<void>();

  bool get isLoggedIn => accessToken != null && user != null;
  bool get isStaff => staffToken != null;
  bool get usingMock => api.usingMock;

  Future<void> waitUntilReady() => _ready.future;

  Future<void> bootstrap() async {
    final prefs = await SharedPreferences.getInstance();
    final theme = prefs.getString('theme_mode');
    themeMode = switch (theme) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
    accessToken = prefs.getString('access_token');
    refreshToken = prefs.getString('refresh_token');
    staffToken = prefs.getString('staff_token');
    final rawUser = prefs.getString('user_json');
    if (rawUser != null) {
      final parts = rawUser.split('|');
      if (parts.length == 3) {
        user = User(id: parts[0], name: parts[1], phone: parts[2]);
      }
    }

    try {
      await api.probe();
      if (accessToken != null) {
        try {
          user = await api.me(accessToken!);
          await _persist();
        } catch (_) {
          if (!api.usingMock) {
            accessToken = null;
            refreshToken = null;
            user = null;
            await _persist();
          }
        }
      }
    } catch (_) {}

    ready = true;
    if (!_ready.isCompleted) _ready.complete();
    notifyListeners();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme_mode', switch (themeMode) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      _ => 'system',
    });
    if (accessToken != null) {
      await prefs.setString('access_token', accessToken!);
    } else {
      await prefs.remove('access_token');
    }
    if (refreshToken != null) {
      await prefs.setString('refresh_token', refreshToken!);
    } else {
      await prefs.remove('refresh_token');
    }
    if (staffToken != null) {
      await prefs.setString('staff_token', staffToken!);
    } else {
      await prefs.remove('staff_token');
    }
    if (user != null) {
      await prefs.setString(
        'user_json',
        '${user!.id}|${user!.name}|${user!.phone}',
      );
    } else {
      await prefs.remove('user_json');
    }
  }

  Future<void> setTheme(ThemeMode mode) async {
    themeMode = mode;
    await _persist();
    notifyListeners();
  }

  void cycleTheme() {
    final next = switch (themeMode) {
      ThemeMode.system => ThemeMode.light,
      ThemeMode.light => ThemeMode.dark,
      ThemeMode.dark => ThemeMode.system,
    };
    setTheme(next);
  }

  Future<void> login(String phone, String password) async {
    final session = await api.login(phone: phone, password: password);
    accessToken = session.access;
    refreshToken = session.refresh;
    user = session.user;
    await _persist();
    notifyListeners();
  }

  Future<void> register(String name, String phone, String password) async {
    final session = await api.register(
      name: name,
      phone: phone,
      password: password,
    );
    accessToken = session.access;
    refreshToken = session.refresh;
    user = session.user;
    await _persist();
    notifyListeners();
  }

  Future<void> logout() async {
    accessToken = null;
    refreshToken = null;
    user = null;
    await _persist();
    notifyListeners();
  }

  Future<void> staffLogin(String pin) async {
    staffToken = await api.staffLogin(pin);
    await _persist();
    notifyListeners();
  }

  Future<void> staffLogout() async {
    staffToken = null;
    await _persist();
    notifyListeners();
  }
}
