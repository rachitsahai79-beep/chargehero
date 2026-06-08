// chargehero_engineer_app/lib/constants.dart

const String API_BASE_URL = 'https://chargehero-api.com/api/v1';
const Duration API_TIMEOUT = Duration(seconds: 30);
const Duration JWT_EXPIRATION = Duration(days: 7);

// Charger types
const List<String> CHARGER_TYPES = [
  '3.3kW',
  '7.4kW',
  '22kW',
  '30kW',
  '60kW',
  '120kW',
  '240kW'
];

// Charger brands
const List<String> CHARGER_BRANDS = [
  'ABB',
  'Delta',
  'Exicom',
  'Servotech'
];

// Ticket types
const Map<String, String> TICKET_TYPES = {
  'preventive_maintenance': 'Preventive Maintenance',
  'commission': 'Commission',
  'issue': 'Issue/Fault'
};

// Priority levels
const Map<String, String> PRIORITY_LEVELS = {
  'low': 'Low',
  'medium': 'Medium',
  'high': 'High',
  'critical': 'Critical'
};
