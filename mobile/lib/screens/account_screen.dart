import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../state/session.dart';
import '../theme/tokens.dart';
import '../widgets/chrome.dart';

class AccountScreen extends StatelessWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionController>();
    final user = session.user;
    final themeLabel = switch (session.themeMode) {
      ThemeMode.light => 'Light',
      ThemeMode.dark => 'Dark',
      ThemeMode.system => 'System',
    };

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Account', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 16),
        if (user != null)
          AppCard(
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: MahgouzColors.courtGreen,
                  foregroundColor: Colors.white,
                  child: Text(user.name.characters.first.toUpperCase()),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user.name,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(
                        user.phone,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          )
        else
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text('Log in to book courts and see your passes.'),
                const SizedBox(height: 12),
                PrimaryButton(
                  label: 'Log in',
                  onPressed: () => context.push('/login'),
                ),
              ],
            ),
          ),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.brightness_6_outlined),
                title: const Text('Theme'),
                subtitle: Text(themeLabel),
                onTap: session.cycleTheme,
              ),
              const Divider(),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.badge_outlined),
                title: const Text('Staff'),
                onTap: () => session.isStaff
                    ? context.go('/staff/bookings')
                    : context.push('/staff/login'),
              ),
              if (user != null) ...[
                const Divider(),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.logout, color: MahgouzColors.error),
                  title: const Text(
                    'Log out',
                    style: TextStyle(color: MahgouzColors.error),
                  ),
                  onTap: () async {
                    await session.logout();
                    if (context.mounted) context.go('/');
                  },
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
