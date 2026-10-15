/// URL base de la API desplegada en Render. Para probar contra un backend local usar, por ejemplo,
/// `http://10.0.2.2:5000` (10.0.2.2 es la PC vista desde el emulador de Android).
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://clubpalomapatinio.onrender.com',
);
