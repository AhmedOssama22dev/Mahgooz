import 'package:flutter/foundation.dart';

class AppConfig {
  static const whatsappUrl = 'https://wa.me/201000000000';
  static const locationLabel = 'Sheikh Zayed • 2 courts';
  static const bookAheadDays = 14;
  static const holdTtl = Duration(minutes: 10);
  static const pollInterval = Duration(seconds: 2);
  static const pollTimeout = Duration(seconds: 60);
  static const requestTimeout = Duration(seconds: 6);

  static String get apiBaseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL');
    if (fromEnv.isNotEmpty) return fromEnv.replaceAll(RegExp(r'/$'), '');
    if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return 'http://10.0.2.2:8000/api/v1';
      default:
        return 'http://127.0.0.1:8000/api/v1';
    }
  }
}

class BrandAssets {
  static const iconGreen = 'assets/brand/mahgouz-icon-green-official.png';
  static const iconDark = 'assets/brand/mahgouz-icon-dark-official.png';
  static const lockupLight = 'assets/brand/mahgouz-lockup-light-official.png';
  static const lockupDark = 'assets/brand/mahgouz-lockup-dark-official.png';
  static const splash = 'assets/brand/mahgouz-splash-dark.png';
  static const hero = 'assets/brand/mahgouz-social-launch.png';
  static const badge = 'assets/brand/mahgouz-logo-badge-sheikh-zayed.png';
  static const appIcon = 'assets/brand/mahgouz-app-icon.png';
}
