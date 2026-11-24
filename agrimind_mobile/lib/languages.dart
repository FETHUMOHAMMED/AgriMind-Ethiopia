import 'package:flutter/foundation.dart';

class AppLanguage {
  static String current = 'en';

  static final Map<String, Map<String, String>> _translations = {
    'en': {
      // Common
      'app_name': 'AgriMind Ethiopia',
      'tagline': 'Detect crop diseases instantly',
      'login': 'Login',
      'register': 'Register',
      'logout': 'Logout',
      'email': 'Email',
      'password': 'Password',
      'full_name': 'Full Name',
      'phone': 'Phone (optional)',
      
      // Messages
      'login_failed': 'Login failed',
      'registration_success': 'Registration successful. Please login.',
      'registration_failed': 'Registration failed',
      'prediction_failed': 'Prediction failed',
      'feedback_submitted': 'Feedback submitted. Thank you!',
      'no_history': 'No predictions yet.\nDiagnose a crop to see history.',
      
      // Home
      'your_ai_crop_doctor': 'Your AI Crop Doctor',
      'diagnose_crop': 'Diagnose Crop',
      'prediction_history': 'Prediction History',
      'my_profile': 'My Profile',
      
      // Upload
      'pick_image': 'Pick Crop Image',
      'detect_disease': 'Detect Disease',
      'disease': 'Disease',
      'confidence': 'Confidence',
      'recommendation': 'Recommendation',
      'symptoms': 'Symptoms',
      'prevention': 'Prevention',
      'expert_advice': 'Expert advice',
      'correct': 'Correct',
      'incorrect': 'Incorrect',
      
      // Profile
      'name': 'Name',
      'language': 'Language',
      'role': 'Role',
      'not_provided': 'Not provided',
      
      // Register
      'already_have_account': 'Already have an account? Login',
      'dont_have_account': 'Don\'t have an account? Register',
    },
    'am': {
      // Common
      'app_name': 'አግሪማይንድ ኢትዮጵያ',
      'tagline': 'የሰብል በሽታዎችን በፍጥነት ይለዩ',
      'login': 'ግባ',
      'register': 'ተመዝገብ',
      'logout': 'ውጣ',
      'email': 'ኢሜይል',
      'password': 'የይለፍ ቃል',
      'full_name': 'ሙሉ ስም',
      'phone': 'ስልክ (አማራጭ)',
      
      // Messages
      'login_failed': 'መግባት አልተሳካም',
      'registration_success': 'ምዝገባ ተሳክቷል። እባክዎ ይግቡ።',
      'registration_failed': 'ምዝገባ አልተሳካም',
      'prediction_failed': 'ትንበያ አልተሳካም',
      'feedback_submitted': 'አስተያየት ተልኳል። እናመሰግናለን!',
      'no_history': 'እስካሁን ምንም ትንበያ የለም።\nሰብልን ይመርምሩ።',
      
      // Home
      'your_ai_crop_doctor': 'የእርስዎ AI የሰብል ሐኪም',
      'diagnose_crop': 'ሰብልን ይመርምሩ',
      'prediction_history': 'የትንበያ ታሪክ',
      'my_profile': 'የእኔ መገለጫ',
      
      // Upload
      'pick_image': 'የሰብል ፎቶ ይምረጡ',
      'detect_disease': 'በሽታን ይለዩ',
      'disease': 'በሽታ',
      'confidence': 'እምነት',
      'symptoms': 'ምልክቶች',
      'prevention': 'መከላከል',
      'expert_advice': 'የባለሙያ ምክር',
      'recommendation': 'ምክረ ሃሳብ',
      'correct': 'ትክክል',
      'incorrect': 'ትክክል አይደለም',
      
      // Profile
      'name': 'ስም',
      'language': 'ቋንቋ',
      'role': 'ሚና',
      'not_provided': 'አልተሰጠም',
      
      // Register
      'already_have_account': 'መለያ አለዎት? ይግቡ',
      'dont_have_account': 'መለያ የለዎትም? ይመዝገቡ',
    },
    'om': {
      // Common
      'app_name': 'AgriMind Itoophiyaa',
      'tagline': 'Dhukkuba midhaanii hatattamaan sakatta\'i',
      'login': 'Galmaa\'i',
      'register': 'Galmaa\'i',
      'logout': 'Ba\'i',
      'email': 'Imeelii',
      'password': 'Jecha darbaa',
      'full_name': 'Maqaa guutuu',
      'phone': 'Bilbila (dirqama miti)',
      
      // Messages
      'login_failed': 'Galmaahi hin milkoofne',
      'registration_success': 'Galmaahi milkoofte. Galmaa\'i.',
      'registration_failed': 'Galmaahi hin milkoofne',
      'prediction_failed': 'Raajiin hin milkoofne',
      'feedback_submitted': 'Yaada kee galmeessine. Galatoomaa!',
      'no_history': 'Raajiin hin jiru.\nMidhaan sakatta\'i.',
      
      // Home
      'your_ai_crop_doctor': 'Doktora Midhaan AI Kee',
      'diagnose_crop': 'Midhaan sakatta\'i',
      'prediction_history': 'Seenaa Raajii',
      'my_profile': 'Profaayilii Koo',
      
      // Upload
      'pick_image': 'Fakkii midhaan filadhu',
      'detect_disease': 'Dhukkuba sakatta\'i',
      'disease': 'Dhukkuba',
      'confidence': 'Amantaa',
      'symptoms': 'Mallattoolee',
      'prevention': 'Ittisa',
      'expert_advice': 'Gorsa ogeessaa',
      'recommendation': 'Gorsa',
      'correct': 'Sirrii',
      'incorrect': 'Dogoggora',
      
      // Profile
      'name': 'Maqaa',
      'language': 'Afaan',
      'role': 'Gahee',
      'not_provided': 'Hin kennamne',
      
      // Register
      'already_have_account': 'Account qabdaa? Galmaa\'i',
      'dont_have_account': 'Account hin qabduu? Galmaa\'i',
    },
  };

    static String t(String key) {
    return _translations[current]?[key] ?? _translations['en']![key] ?? key;
  }

  static final ValueNotifier<String> notifier = ValueNotifier('en');

  static void setLanguage(String lang) {
    current = lang;
    notifier.value = lang;
  }
}