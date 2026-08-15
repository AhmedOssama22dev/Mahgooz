import 'package:flutter_test/flutter_test.dart';
import 'package:mahgouz/models.dart';
import 'package:mahgouz/util/format.dart';

void main() {
  test('formats EGP and slot periods', () {
    expect(formatEgp(350), 'EGP 350');
    expect(periodForHour(9), 'morning');
    expect(periodForHour(14), 'afternoon');
    expect(priceForPeriod('evening'), 350);
    expect(isEgyptianPhone('01012345678'), isTrue);
    expect(isEgyptianPhone('123'), isFalse);
  });

  test('parses court JSON from the API contract', () {
    final court = Court.fromJson({
      'id': '11111111-1111-4111-8111-111111111111',
      'name': 'Court 1',
      'slug': 'court-1',
    });
    expect(court.name, 'Court 1');
  });
}
