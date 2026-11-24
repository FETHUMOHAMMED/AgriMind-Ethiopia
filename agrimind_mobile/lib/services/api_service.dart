import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiService {
  static String get baseUrl => ApiConfig.baseUrl;

  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  // ------------------------------------------------------------------
  // Authentication
  // ------------------------------------------------------------------
  Future<Map<String, dynamic>> register({
    required String fullName,
    required String email,
    required String password,
    String? phone,
    String language = 'en',
  }) async {
    final response = await _dio.post('/auth/register', data: {
      'full_name': fullName,
      'email': email,
      'password': password,
      'phone': phone,
      'language': language,
    });
    return response.data;
  }

  Future<String> login({
  required String email,
  required String password,
}) async {
  try {
    final response = await _dio.post(
      '/auth/login',
      data: {
        'email': email,
        'password': password,
      },
    );

    final token = response.data['access_token'];

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);

    return token;
  } on DioException {
    throw Exception('Failed to login');
  }
}

  // ------------------------------------------------------------------
  // Predictions
  // ------------------------------------------------------------------
  /// Send a file path (mobile) to the backend
  Future<Map<String, dynamic>> predictDisease(
      String filePath, String token) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    final response = await _dio.post(
      '/predict/',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  /// Send raw bytes (web) to the backend
  Future<Map<String, dynamic>> predictDiseaseFromBytes(
    Uint8List bytes, String token) async {
  final formData = FormData.fromMap({
    'file': MultipartFile.fromBytes(bytes, filename: 'leaf.jpg'),
  });
  final response = await _dio.post(
    '/predict/',
    data: formData,
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return response.data;
}

  /// Get prediction history for the logged-in user
  Future<List<dynamic>> getHistory(String token) async {
    final response = await _dio.get(
      '/predict/history',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  /// Get dashboard statistics
  Future<Map<String, dynamic>> getStats(String token) async {
    final response = await _dio.get(
      '/predict/stats',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  /// Get recent predictions
  Future<List<dynamic>> getRecent(String token) async {
    final response = await _dio.get(
      '/predict/recent',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  /// Get disease summary (count per disease)
  Future<List<dynamic>> getDiseaseSummary(String token) async {
    final response = await _dio.get(
      '/predict/disease-summary',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  // ------------------------------------------------------------------
  // User Profile
  // ------------------------------------------------------------------
  Future<Map<String, dynamic>> getUserProfile(String token) async {
    final response = await _dio.get(
      '/users/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data;
  }

  // ------------------------------------------------------------------
  // Feedback
  // ------------------------------------------------------------------
  Future<void> submitFeedback({
    required int predictionId,
    required bool correct,
    required String comment,
    required String token,
  }) async {
    await _dio.post(
      '/feedback/',
      data: {
        'prediction_id': predictionId,
        'correct': correct,
        'comment': comment,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }
}