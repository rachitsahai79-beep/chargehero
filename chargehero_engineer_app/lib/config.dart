// chargehero_engineer_app/lib/config.dart
import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static final AppConfig _instance = AppConfig._internal();

  late String apiBaseUrl;
  late String supabaseUrl;
  late String supabaseAnonKey;
  late String firebaseProjectId;
  late String googleMapsApiKey;

  factory AppConfig() {
    return _instance;
  }

  AppConfig._internal();

  Future<void> initialize() async {
    await dotenv.load(fileName: '.env');

    apiBaseUrl = dotenv.env['API_BASE_URL'] ?? 'https://chargehero-api.com/api/v1';
    supabaseUrl = dotenv.env['SUPABASE_URL'] ?? '';
    supabaseAnonKey = dotenv.env['SUPABASE_ANON_KEY'] ?? '';
    firebaseProjectId = dotenv.env['FIREBASE_PROJECT_ID'] ?? '';
    googleMapsApiKey = dotenv.env['GOOGLE_MAPS_API_KEY'] ?? '';
  }
}
