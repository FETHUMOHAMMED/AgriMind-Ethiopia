import 'package:flutter/material.dart';
import 'languages.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const AgriMindApp());
}

class AgriMindApp extends StatefulWidget {
  const AgriMindApp({super.key});

  @override
  State<AgriMindApp> createState() => _AgriMindAppState();
}

class _AgriMindAppState extends State<AgriMindApp> {
  @override
  void initState() {
    super.initState();
    AppLanguage.notifier.addListener(_onLanguageChanged);
  }

  void _onLanguageChanged() {
    setState(() {});
  }

  @override
  void dispose() {
    AppLanguage.notifier.removeListener(_onLanguageChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AgriMind Ethiopia',
      home: LoginScreen(key: ValueKey(AppLanguage.current)),
    );
  }
}