import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../languages.dart';
import '../services/api_service.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _api = ApiService();
  Map<String, dynamic>? _user;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token') ?? '';
      if (token.isNotEmpty) {
        final user = await _api.getUserProfile(token);

        // ✅ Guard after await
        if (!mounted) return;

        setState(() {
          _user = user;
          _loading = false;
        });
      } else {
        if (mounted) setState(() => _loading = false);
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');

    // ✅ Guard after await
    if (!mounted) return;

    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(AppLanguage.t('my_profile'))),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _user == null
              ? const Center(child: Text('Error loading profile'))
              : Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const CircleAvatar(
                        radius: 40,
                        child: Icon(Icons.person, size: 40),
                      ),
                      const SizedBox(height: 20),
                      Text(
                        '${AppLanguage.t('name')}: ${_user!['full_name'] ?? AppLanguage.t('not_provided')}',
                        style: const TextStyle(fontSize: 18),
                      ),
                      const SizedBox(height: 12),
                      Text(
                          '${AppLanguage.t('email')}: ${_user!['email'] ?? ''}'),
                      const SizedBox(height: 12),
                      Text(
                          '${AppLanguage.t('language')}: ${_user!['language'] ?? 'en'}'),
                      const SizedBox(height: 12),
                      Text(
                          '${AppLanguage.t('role')}: ${_user!['role'] ?? 'farmer'}'),
                      const SizedBox(height: 40),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          onPressed: _logout,
                          icon: const Icon(Icons.logout),
                          label: Text(AppLanguage.t('logout')),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}