class Config {
  /// Base URL for the ChargeHero backend API.
  ///
  /// Defaults to the live Railway deployment. Override for local development:
  ///   flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1
  /// (On the Android emulator use http://10.0.2.2:8000/api/v1 to reach the host.)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://chargehero-production.up.railway.app/api/v1',
  );

  static const String appName = 'ChargeHero Customer';
  static const String appVersion = '1.0.0';
}
