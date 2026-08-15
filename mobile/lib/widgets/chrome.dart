import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../config.dart';
import '../theme/tokens.dart';

class MahgouzMark extends StatelessWidget {
  const MahgouzMark({
    super.key,
    this.size = 28,
    this.showWordmark = true,
    this.light = true,
  });

  final double size;
  final bool showWordmark;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final ink = Theme.of(context).colorScheme.onSurface;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Image.asset(
          light ? BrandAssets.iconGreen : BrandAssets.iconDark,
          width: size,
          height: size,
          filterQuality: FilterQuality.high,
        ),
        if (showWordmark) ...[
          const SizedBox(width: 8),
          Text(
            'Mahgouz',
            style: GoogleFonts.dmSans(
              fontWeight: FontWeight.w700,
              fontSize: size * 0.72,
              color: ink,
              height: 1,
            ),
          ),
        ],
      ],
    );
  }
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(MahgouzRadii.md),
        boxShadow: dark && onPressed != null
            ? const [MahgouzColors.ctaGlow]
            : null,
      ),
      child: FilledButton(
        onPressed: loading ? null : onPressed,
        child: loading
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 20),
                    const SizedBox(width: 8),
                  ],
                  Text(label),
                ],
              ),
      ),
    );
  }
}

class AppCard extends StatelessWidget {
  const AppCard({super.key, required this.child, this.padding, this.onTap});

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final card = Card(
      child: Padding(
        padding: padding ?? const EdgeInsets.all(MahgouzSpace.md),
        child: child,
      ),
    );
    if (onTap == null) return card;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(MahgouzRadii.md),
      child: card,
    );
  }
}

class MockBanner extends StatelessWidget {
  const MockBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: MahgouzColors.clayOrange.withValues(alpha: 0.14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            const Icon(
              Icons.wifi_off_rounded,
              size: 16,
              color: MahgouzColors.clayOrange,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Offline · using demo data',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: MahgouzColors.clayOrange,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ScreenBody extends StatelessWidget {
  const ScreenBody({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(MahgouzSpace.md),
  });

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
