import 'package:go_router/go_router.dart';

import 'screens/account_screen.dart';
import 'screens/auth_screens.dart';
import 'screens/book_screen.dart';
import 'screens/bookings_screen.dart';
import 'screens/customer_shell.dart';
import 'screens/landing_screen.dart';
import 'screens/pass_screen.dart';
import 'screens/payment_screens.dart';
import 'screens/splash_screen.dart';
import 'screens/staff_screens.dart';
import 'state/session.dart';

GoRouter createRouter(SessionController session) {
  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: session,
    redirect: (context, state) {
      final loc = state.uri.path;
      if (!session.ready && loc != '/splash') return '/splash';
      if (loc == '/splash') return null;

      final loggingIn = loc == '/login' || loc == '/register';
      final staffGate = loc.startsWith('/staff');
      final staffLogin = loc == '/staff/login';
      final needsAuth =
          loc == '/book' || loc.startsWith('/book/') || loc == '/bookings';

      if (needsAuth && !session.isLoggedIn) {
        return '/login?next=${Uri.encodeComponent(state.uri.toString())}';
      }
      if (loggingIn && session.isLoggedIn) {
        return state.uri.queryParameters['next'] ?? '/book';
      }
      if (staffGate && !staffLogin && !session.isStaff) {
        return '/staff/login';
      }
      if (staffLogin && session.isStaff) return '/staff/bookings';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const SplashScreen()),
      GoRoute(
        path: '/login',
        builder: (_, state) =>
            LoginScreen(next: state.uri.queryParameters['next']),
      ),
      GoRoute(
        path: '/register',
        builder: (_, state) =>
            RegisterScreen(next: state.uri.queryParameters['next']),
      ),
      GoRoute(
        path: '/book/pending',
        builder: (_, state) =>
            PendingScreen(bookingId: state.uri.queryParameters['id'] ?? ''),
      ),
      GoRoute(path: '/book/failed', builder: (_, _) => const FailedScreen()),
      GoRoute(
        path: '/pass/:code',
        builder: (_, state) => PassScreen(code: state.pathParameters['code']!),
      ),
      GoRoute(
        path: '/staff/login',
        builder: (_, _) => const StaffLoginScreen(),
      ),
      GoRoute(path: '/staff', builder: (_, _) => const StaffLookupScreen()),
      GoRoute(
        path: '/staff/bookings',
        builder: (_, _) => const StaffBookingsScreen(),
      ),
      GoRoute(
        path: '/staff/pass/:code',
        builder: (_, state) =>
            StaffPassScreen(code: state.pathParameters['code']!),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) =>
            CustomerShell(navigationShell: shell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/', builder: (_, _) => const LandingScreen()),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/book',
                builder: (_, state) =>
                    BookScreen(period: state.uri.queryParameters['period']),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/bookings',
                builder: (_, _) => const BookingsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/account',
                builder: (_, _) => const AccountScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
}
