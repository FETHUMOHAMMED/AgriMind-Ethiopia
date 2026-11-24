import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../languages.dart';
import '../services/api_service.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  XFile? _pickedFile;
  final _picker = ImagePicker();
  final _apiService = ApiService();
  Map<String, dynamic>? _result;
  bool _isPredicting = false;

  /// Uncertain = backend explicitly says so, OR numeric confidence < 0.30
  bool get _isUncertain {
    if (_result == null) return false;
    final name = _result!['disease'];
    if (name == 'Unknown / Uncertain') return true;
    final conf = _result!['confidence'];
    if (conf is num && conf.toDouble() < 0.30) return true;
    return false;
  }

  Future<void> _pickImage() async {
    final XFile? picked = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
    );
    if (picked != null) {
      setState(() {
        _pickedFile = picked;
        _result = null;
      });
    }
  }

  Future<void> _predict() async {
    if (_pickedFile == null) return;
    setState(() => _isPredicting = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token') ?? '';
      final bytes = await _pickedFile!.readAsBytes();

      Map<String, dynamic> prediction;
      if (kIsWeb) {
        prediction =
            await _apiService.predictDiseaseFromBytes(bytes, token);
      } else {
        prediction =
            await _apiService.predictDisease(_pickedFile!.path, token);
      }

      // ✅ Guard after await
      if (!mounted) return;

      setState(() => _result = prediction);
    } catch (e) {
      // ✅ Guard in catch
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content:
                Text('${AppLanguage.t('prediction_failed')}: $e')),
      );
    } finally {
      if (mounted) setState(() => _isPredicting = false);
    }
  }

  Future<void> _submitFeedback(bool correct) async {
    // Safety: no feedback for uncertain results
    if (_result == null || _isUncertain) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token') ?? '';
      await _apiService.submitFeedback(
        predictionId: _result!['prediction_id'],
        correct: correct,
        comment: '',
        token: token,
      );

      // ✅ Guard after await
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLanguage.t('feedback_submitted'))),
      );
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(AppLanguage.t('diagnose_crop')),
        leading: BackButton(),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            // ---------- Image preview ----------
            if (_pickedFile != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: kIsWeb
                    ? Image.network(_pickedFile!.path,
                        height: 200, fit: BoxFit.cover)
                    : Image.file(File(_pickedFile!.path),
                        height: 200, fit: BoxFit.cover),
              ),
            const SizedBox(height: 16),

            // ---------- Pick image ----------
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                    vertical: 14, horizontal: 24),
              ),
              onPressed: _pickImage,
              icon: const Icon(Icons.photo_library),
              label: Text(AppLanguage.t('pick_image')),
            ),
            const SizedBox(height: 12),

            // ---------- Detect ----------
            if (_pickedFile != null && !_isPredicting)
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                      vertical: 14, horizontal: 24),
                ),
                onPressed: _predict,
                icon: const Icon(Icons.search),
                label: Text(AppLanguage.t('detect_disease')),
              ),
            if (_isPredicting)
              const Column(
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 12),
                  Text('Analyzing crop image...'),
                ],
              ),
            const SizedBox(height: 20),

            // ---------- Result card ----------
            if (_result != null)
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                color: _isUncertain ? Colors.orange.shade50 : Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Uncertain warning
                      if (_isUncertain)
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.orange.shade100,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.warning_amber,
                                  color: Colors.orange),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Low confidence — please verify with an expert',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: Colors.orange,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      if (_isUncertain) const SizedBox(height: 16),

                      // Disease name
                      Row(
                        children: [
                          Icon(
                            _isUncertain
                                ? Icons.help_outline
                                : Icons.bug_report,
                            color:
                                _isUncertain ? Colors.orange : Colors.red,
                            size: 28,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '${AppLanguage.t('disease')}: ${_result!['disease']}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const Divider(height: 24),

                      // Confidence
                      Row(
                        children: [
                          Text('${AppLanguage.t('confidence')}: '),
                          Text(
                            _result!['confidence'] is num
                                ? '${((_result!['confidence'] as num) * 100).toStringAsFixed(1)}%'
                                : 'N/A',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: (_result!['confidence'] is num &&
                                      (_result!['confidence'] as num) >
                                          0.50)
                                  ? Colors.green
                                  : Colors.orange,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Recommendation
                      Text(
                        AppLanguage.t('recommendation'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(_result!['recommendation'] ?? ''),
                      const SizedBox(height: 12),

                      // Symptoms
                      Text(
                        AppLanguage.t('symptoms'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(_result!['symptoms'] ?? 'N/A'),
                      const SizedBox(height: 12),

                      // Prevention
                      Text(
                        AppLanguage.t('prevention'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(_result!['prevention'] ?? 'N/A'),
                      const SizedBox(height: 12),

                      // Expert help
                      Text(
                        AppLanguage.t('expert_advice'),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _result!['expert_help'] ?? 'N/A',
                        style: const TextStyle(fontStyle: FontStyle.italic),
                      ),
                      const SizedBox(height: 16),

                      // Feedback buttons (hidden for uncertain)
                      if (!_isUncertain)
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            ElevatedButton.icon(
                              onPressed: () => _submitFeedback(true),
                              icon: const Icon(Icons.thumb_up, size: 16),
                              label: Text(AppLanguage.t('correct')),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                              ),
                            ),
                            ElevatedButton.icon(
                              onPressed: () => _submitFeedback(false),
                              icon: const Icon(Icons.thumb_down, size: 16),
                              label: Text(AppLanguage.t('incorrect')),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.red,
                                foregroundColor: Colors.white,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}