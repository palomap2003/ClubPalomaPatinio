import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

const kNeon = Color(0xFFD4FF00);
const kBg = Color(0xFF0B0C16);
const kCard = Color(0xFF171A24);
const kError = Color(0xFFFF5959);

Color blanco(double opacidad) => Colors.white.withValues(alpha: opacidad);

ThemeData buildTheme() {
  final base = ThemeData(
    brightness: Brightness.dark,
    useMaterial3: true,
    scaffoldBackgroundColor: kBg,
    colorScheme: const ColorScheme.dark(
      primary: kNeon,
      onPrimary: Colors.black,
      surface: kBg,
      error: kError,
    ),
  );
  final inputBorder = OutlineInputBorder(
    borderRadius: BorderRadius.circular(12),
    borderSide: BorderSide(color: blanco(0.12)),
  );
  return base.copyWith(
    textTheme: GoogleFonts.interTextTheme(base.textTheme),
    appBarTheme: const AppBarTheme(backgroundColor: kBg, elevation: 0, scrolledUnderElevation: 0),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: blanco(0.06),
      border: inputBorder,
      enabledBorder: inputBorder,
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: kNeon),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: kError),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: kError),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: kNeon,
        foregroundColor: Colors.black,
        disabledBackgroundColor: kNeon.withValues(alpha: 0.35),
        disabledForegroundColor: Colors.black54,
        minimumSize: const Size.fromHeight(50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: GoogleFonts.barlowCondensed(fontSize: 18, fontWeight: FontWeight.w800, letterSpacing: 0.6),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        minimumSize: const Size.fromHeight(50),
        side: BorderSide(color: blanco(0.2)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: kCard,
      indicatorColor: kNeon.withValues(alpha: 0.2),
    ),
  );
}

TextStyle titulo(double size) =>
    GoogleFonts.barlowCondensed(fontSize: size, fontWeight: FontWeight.w800, color: Colors.white);
