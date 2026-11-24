import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../languages.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final ApiService _api = ApiService();
  List<dynamic>? _predictions;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token') ?? '';
      if (token.isNotEmpty) {
        final history = await _api.getHistory(token);
        setState(() {
          _predictions = history;
          _loading = false;
        });
      } else {
        setState(() => _loading = false);
      }
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
  title: Text(AppLanguage.t('prediction_history')),
  leading: IconButton(
    icon: const Icon(Icons.arrow_back),
    onPressed: () {
  Navigator.pop(context);
},
  ),
),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _predictions == null || _predictions!.isEmpty
              ? Center(
  child: Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      const Icon(Icons.history, size: 64, color: Colors.grey),
      const SizedBox(height: 16),
      Text(
        AppLanguage.t('no_history'),
        textAlign: TextAlign.center,
        style: const TextStyle(fontSize: 16, color: Colors.grey),
      ),
    ],
  ),
)
              : ListView.builder(
                  itemCount: _predictions!.length,
                  itemBuilder: (context, index) {
                    final p = _predictions![index];
                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                      child: ListTile(
                        title: Text(
                          p['disease'] ?? 'Unknown',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          '${AppLanguage.t('confidence')}: ${(p['confidence'] * 100).toStringAsFixed(1)}%',
                        ),
                        trailing: Text(
                          p['created_at']?.toString().substring(0, 10) ?? '',
                          style: const TextStyle(color: Colors.grey),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}