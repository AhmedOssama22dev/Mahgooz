import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'router.dart';
import 'state/session.dart';
import 'theme/app_theme.dart';

class MahgouzApp extends StatefulWidget {
  const MahgouzApp({super.key});

  @override
  State<MahgouzApp> createState() => _MahgouzAppState();
}

class _MahgouzAppState extends State<MahgouzApp> {
  late final SessionController _session;
  late final router = createRouter(_session);

  @override
  void initState() {
    super.initState();
    _session = SessionController()..bootstrap();
  }

  @override
  void dispose() {
    _session.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _session,
      child: Consumer<SessionController>(
        builder: (context, session, _) {
          return MaterialApp.router(
            title: 'Mahgouz',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light(),
            darkTheme: AppTheme.dark(),
            themeMode: session.themeMode,
            routerConfig: router,
          );
        },
      ),
    );
  }
}
