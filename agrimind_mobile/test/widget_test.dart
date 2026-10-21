import 'package:flutter_test/flutter_test.dart';
import 'package:agrimind_mobile/main.dart';

void main() {
  testWidgets('AgriMind app loads without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const AgriMindApp());

    // Smoke test: the app builds without throwing.
    // If AgriMindApp is present in the widget tree, the test passes.
    expect(find.byType(AgriMindApp), findsOneWidget);
  });
}