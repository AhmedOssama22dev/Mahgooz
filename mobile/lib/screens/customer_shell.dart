import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../state/session.dart';
import '../theme/tokens.dart';
import '../widgets/chrome.dart';

class CustomerShell extends StatelessWidget {
  const CustomerShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionController>();
    return Scaffold(
      appBar: AppBar(
        title: MahgouzMark(
          light: Theme.of(context).brightness == Brightness.light,
        ),
        actions: [
          IconButton(
            tooltip: 'Theme',
            onPressed: session.cycleTheme,
            icon: Icon(
              session.themeMode == ThemeMode.dark
                  ? Icons.dark_mode
                  : session.themeMode == ThemeMode.light
                  ? Icons.light_mode
                  : Icons.brightness_auto,
            ),
          ),
          if (!session.isLoggedIn && navigationShell.currentIndex == 0)
            TextButton(
              onPressed: () => context.push('/login'),
              child: const Text('Log in'),
            )
          else if (session.isLoggedIn)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: CircleAvatar(
                radius: 14,
                backgroundColor: MahgouzColors.courtGreen,
                foregroundColor: Colors.white,
                child: Text(
                  (session.user?.name ?? 'M').characters.first.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          if (session.usingMock) const MockBanner(),
          Expanded(child: navigationShell),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          if ((index == 1 || index == 2) && !session.isLoggedIn) {
            context.push('/login?next=${index == 1 ? '/book' : '/bookings'}');
            return;
          }
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          );
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month),
            label: 'Book',
          ),
          NavigationDestination(
            icon: Icon(Icons.confirmation_number_outlined),
            selectedIcon: Icon(Icons.confirmation_number),
            label: 'Bookings',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Account',
          ),
        ],
      ),
    );
  }
}
