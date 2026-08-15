import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'tokens.dart';

abstract final class AppTheme {
  static ThemeData light() => _build(
    brightness: Brightness.light,
    bg: MahgouzColors.lightBg,
    surface: MahgouzColors.lightSurface,
    elevated: MahgouzColors.lightSurface,
    border: MahgouzColors.lightBorder,
    ink: MahgouzColors.lightInk,
    muted: MahgouzColors.lightMuted,
  );

  static ThemeData dark() => _build(
    brightness: Brightness.dark,
    bg: MahgouzColors.darkBg,
    surface: MahgouzColors.darkSurface,
    elevated: MahgouzColors.darkElevated,
    border: MahgouzColors.darkBorder,
    ink: MahgouzColors.darkInk,
    muted: MahgouzColors.darkMuted,
  );

  static ThemeData _build({
    required Brightness brightness,
    required Color bg,
    required Color surface,
    required Color elevated,
    required Color border,
    required Color ink,
    required Color muted,
  }) {
    final isDark = brightness == Brightness.dark;
    final dmSans = GoogleFonts.dmSansTextTheme().apply(
      bodyColor: ink,
      displayColor: ink,
    );
    final inter = GoogleFonts.interTextTheme().apply(
      bodyColor: ink,
      displayColor: ink,
    );

    final scheme = ColorScheme(
      brightness: brightness,
      primary: MahgouzColors.courtGreen,
      onPrimary: Colors.white,
      secondary: MahgouzColors.clayOrange,
      onSecondary: Colors.white,
      error: MahgouzColors.error,
      onError: Colors.white,
      surface: surface,
      onSurface: ink,
      onSurfaceVariant: muted,
      outline: border,
      outlineVariant: border,
      primaryContainer: isDark
          ? MahgouzColors.slotAvailableDark
          : MahgouzColors.courtGreenLight,
      onPrimaryContainer: MahgouzColors.courtGreenDark,
      tertiary: MahgouzColors.clayOrange,
      onTertiary: Colors.white,
      surfaceContainerHighest: elevated,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: bg,
      canvasColor: bg,
      dividerColor: border,
      textTheme: inter.copyWith(
        displayLarge: dmSans.displayLarge?.copyWith(
          fontWeight: FontWeight.w700,
          fontSize: 32,
          height: 1.15,
          color: ink,
        ),
        headlineLarge: dmSans.headlineLarge?.copyWith(
          fontWeight: FontWeight.w700,
          fontSize: 24,
          height: 1.2,
          color: ink,
        ),
        headlineMedium: dmSans.headlineMedium?.copyWith(
          fontWeight: FontWeight.w600,
          fontSize: 20,
          height: 1.25,
          color: ink,
        ),
        titleLarge: dmSans.titleLarge?.copyWith(
          fontWeight: FontWeight.w600,
          fontSize: 17,
          height: 1.3,
          color: ink,
        ),
        titleMedium: inter.titleMedium?.copyWith(
          fontWeight: FontWeight.w600,
          fontSize: 16,
          color: ink,
        ),
        bodyLarge: inter.bodyLarge?.copyWith(
          fontSize: 16,
          height: 1.5,
          color: ink,
        ),
        bodyMedium: inter.bodyMedium?.copyWith(
          fontSize: 14,
          height: 1.45,
          color: muted,
        ),
        labelLarge: inter.labelLarge?.copyWith(
          fontWeight: FontWeight.w600,
          fontSize: 16,
          color: ink,
        ),
        labelMedium: inter.labelMedium?.copyWith(
          fontWeight: FontWeight.w500,
          fontSize: 14,
          color: ink,
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: bg,
        foregroundColor: ink,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.dmSans(
          fontWeight: FontWeight.w700,
          fontSize: 20,
          color: ink,
        ),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: isDark ? 0 : 1,
        shadowColor: const Color(0x0F0F1A14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
          side: BorderSide(color: border),
        ),
        margin: EdgeInsets.zero,
      ),
      dividerTheme: DividerThemeData(color: border, space: 1, thickness: 1),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        hintStyle: TextStyle(color: muted),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
          borderSide: const BorderSide(
            color: MahgouzColors.courtGreen,
            width: 1.5,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
          borderSide: const BorderSide(color: MahgouzColors.error),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style:
            FilledButton.styleFrom(
              backgroundColor: MahgouzColors.courtGreen,
              foregroundColor: Colors.white,
              minimumSize: const Size.fromHeight(52),
              textStyle: GoogleFonts.inter(
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(MahgouzRadii.md),
              ),
            ).copyWith(
              overlayColor: WidgetStatePropertyAll(
                MahgouzColors.courtGreenDark.withValues(alpha: 0.2),
              ),
            ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: MahgouzColors.courtGreen,
          backgroundColor: surface,
          minimumSize: const Size.fromHeight(52),
          side: BorderSide(color: border),
          textStyle: GoogleFonts.inter(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(MahgouzRadii.md),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: MahgouzColors.courtGreen,
          textStyle: GoogleFonts.inter(
            fontWeight: FontWeight.w600,
            fontSize: 15,
          ),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: ink,
        contentTextStyle: GoogleFonts.inter(color: surface),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(MahgouzRadii.md),
        ),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: MahgouzColors.courtGreen,
        unselectedItemColor: muted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: GoogleFonts.inter(
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
        unselectedLabelStyle: GoogleFonts.inter(fontSize: 12),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surface,
        indicatorColor: isDark
            ? MahgouzColors.slotAvailableDark
            : MahgouzColors.courtGreenLight,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return GoogleFonts.inter(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
            color: selected ? MahgouzColors.courtGreen : muted,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(
            color: selected ? MahgouzColors.courtGreen : muted,
            size: 22,
          );
        }),
      ),
    );
  }
}
