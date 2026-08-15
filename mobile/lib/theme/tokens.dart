import 'package:flutter/material.dart';

/// Brand accents never change between light and dark — only surfaces invert.
abstract final class MahgouzColors {
  static const courtGreen = Color(0xFF1B7A4E);
  static const courtGreenDark = Color(0xFF145C3A);
  static const courtGreenLight = Color(0xFFD4EDDF);
  static const clayOrange = Color(0xFFE86A2A);
  static const clayOrangeLight = Color(0xFFFDE8DC);
  static const error = Color(0xFFC0392B);
  static const redeemed = Color(0xFF6B7280);

  static const lightBg = Color(0xFFF4F7F5);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightBorder = Color(0xFFE2E8E4);
  static const lightInk = Color(0xFF0F1A14);
  static const lightMuted = Color(0xFF5C6B62);
  static const slotAvailableLight = Color(0xFFD4EDDF);
  static const slotHeldLight = Color(0xFFFFF3CD);
  static const slotHeldTextLight = Color(0xFF856404);
  static const slotBookedLight = Color(0xFFE8EAEC);

  static const darkBg = Color(0xFF0F1A14);
  static const darkSurface = Color(0xFF1A2620);
  static const darkElevated = Color(0xFF223029);
  static const darkBorder = Color(0xFF2D4035);
  static const darkInk = Color(0xFFF4F7F5);
  static const darkMuted = Color(0xFF8FA396);
  static const slotAvailableDark = Color(0x2E1B7A4E);
  static const slotHeldDark = Color(0x38856404);
  static const slotHeldTextDark = Color(0xFFD4A843);
  static const slotBookedDark = Color(0xFF1E2A24);
  static const promoDark = Color(0x1FE86A2A);

  static const ctaGlow = BoxShadow(color: Color(0x261B7A4E), blurRadius: 24);
}

abstract final class MahgouzRadii {
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const full = 999.0;
}

abstract final class MahgouzSpace {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
}
