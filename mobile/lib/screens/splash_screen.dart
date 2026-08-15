import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../config.dart';
import '../state/session.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _go());
  }

  Future<void> _go() async {
    final session = context.read<SessionController>();
    if (!session.ready) {
      await Future.any([
        session.waitUntilReady(),
        Future<void>.delayed(const Duration(seconds: 8)),
      ]);
    }
    await Future<void>.delayed(const Duration(milliseconds: 700));
    if (!mounted) return;
    context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1A14),
      body: SizedBox.expand(
        child: Image.asset(BrandAssets.splash, fit: BoxFit.cover),
      ),
    );
  }
}
