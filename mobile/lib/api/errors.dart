class ApiException implements Exception {
  ApiException({
    required this.statusCode,
    required this.code,
    required this.message,
    this.details,
  });

  final int statusCode;
  final String code;
  final String message;
  final Map<String, dynamic>? details;

  factory ApiException.fromBody(int statusCode, Map<String, dynamic> json) {
    final error = json['error'];
    if (error is Map<String, dynamic>) {
      return ApiException(
        statusCode: statusCode,
        code: error['code'] as String? ?? 'ERROR',
        message: error['message'] as String? ?? 'Something went wrong.',
        details: error['details'] as Map<String, dynamic>?,
      );
    }
    return ApiException(
      statusCode: statusCode,
      code: 'ERROR',
      message: 'Something went wrong.',
    );
  }

  @override
  String toString() => message;
}

class NetworkException implements Exception {
  NetworkException([
    this.message = 'Could not reach Mahgouz. Using demo data.',
  ]);

  final String message;

  @override
  String toString() => message;
}
