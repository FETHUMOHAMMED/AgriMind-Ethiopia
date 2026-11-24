// ============================================================
// AGRIMIND API CONFIGURATION
// ============================================================
// This file controls which backend URL the app uses.
//
// TO SWITCH ENVIRONMENTS:
//   Change the value of `_environment` below to 'dev' or 'prod'
//
// TO UPDATE YOUR PC IP:
//   Change the value of `_devPcIp` below
// ============================================================

class ApiConfig {
  // -----------------------------------------------------------
  // ENVIRONMENT SELECTOR — change only this line
  // 'dev'  = Local development (your PC)
  // 'prod' = Cloud deployment
  // -----------------------------------------------------------
  static const String _environment = 'dev';

  // -----------------------------------------------------------
  // DEVELOPMENT URLS
  // -----------------------------------------------------------

  // For Chrome on the same PC
  static const String _devLocalhost = 'http://localhost:8000';

  // For physical Android phone on same WiFi
  // Update this if your PC IP changes
  static const String _devPcIp = 'http://192.168.8.4:8000';

  // For Android emulator (special alias)
  static const String _devEmulator = 'http://10.0.2.2:8000';

  // -----------------------------------------------------------
  // PRODUCTION URL — fill this after cloud deployment
  // -----------------------------------------------------------
  static const String _prodUrl = 'https://agrimind-api.onrender.com';

  // -----------------------------------------------------------
  // ACTIVE URL — do not change below this line
  // -----------------------------------------------------------
  static String get baseUrl {
    if (_environment == 'prod') {
      return _prodUrl;
    }
    // Development: use PC IP by default
    return _devPcIp;
  }

  // Optional: get all dev URLs for quick reference
  static String get devLocalhost => _devLocalhost;
  static String get devPcIp => _devPcIp;
  static String get devEmulator => _devEmulator;
  static String get prodUrl => _prodUrl;
  static String get currentEnvironment => _environment;
}