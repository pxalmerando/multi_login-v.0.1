import pytest
from src.exception_handler import (
    ApiError, ClientError, ServerError, BadRequestError, 
    UnauthorizedError, ForbiddenError, TooManyRequestsError, 
    InternalServerError, ExceptionMapper, handle_api_errors
)

STATUS_CODE_MAPPING = {
    400: BadRequestError,
    401: UnauthorizedError, 
    403: ForbiddenError,
    429: TooManyRequestsError,
    500: InternalServerError
}

ALL_API_ERROR_CLASSES = [
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    TooManyRequestsError,
    InternalServerError
]

SUCCESS_STATUS_CODES = [200, 201, 204, 301, 302, 399]
ERROR_STATUS_CODES = [404, 503]
BOUNDARY_STATUS_CODES = [399, 400, 499, 500, 599, 9999]

@pytest.fixture
def sample_response_data():
    return {'detail': 'Test details', 'code': 'ERROR CODE'}

@pytest.fixture
def sample_error_response():
    return {'error': 'validation_field', 'details': 'Invalid input provided'}

@pytest.fixture
def bad_request_error():
    return BadRequestError(message='Validation failed', invalid_fields=['email', 'password'])

@pytest.fixture
def rate_limit_error():
    return TooManyRequestsError(message='Rate limit exceeded', retry_after=60, limit=100)

@pytest.fixture
def forbidden_error():
    return ForbiddenError(message='Access denied', required_permissions="admin")

@pytest.fixture
def internal_server_error():
    return InternalServerError(message='Database error', error_id='ERR-DB-001')

class TestApiErrorInitialization:
    def test_default_values(self):
        error = ApiError()
        assert error.message == "An API error occurred"
        assert error.status_code == 500
        assert error.response is None
        assert error.error_code == "ApiError"

    def test_custom_initialization(self, sample_response_data):
        error = ApiError(
            message="Custom error",
            status_code=404,
            response=sample_response_data,
            error_code="CustomError"
        )
        assert error.message == "Custom error"
        assert error.status_code == 404
        assert error.response == sample_response_data
        assert error.error_code == "CustomError"

class TestApiErrorRepresentation:
    def test_str_representation(self):
        error = ApiError(message="Test error", status_code=404)
        assert str(error) == "[404] Test error"

    def test_repr_representation(self):
        error = ApiError(message="Test error", status_code=404)
        assert repr(error) == "ApiError(status_code=404, message=Test error)"

class TestApiErrorSerialization:
    def test_to_dict_with_all_fields(self, sample_response_data):
        error = ApiError(message="Test error", status_code=404, response=sample_response_data)
        result = error.to_dict()
        assert result["message"] == "Test error"
        assert result["status_code"] == 404
        assert result["response"] == sample_response_data
        assert result["type"] == "api_error"

    def test_to_dict_with_minimal_fields(self):
        error = ApiError()
        result = error.to_dict()
        assert result["message"] == "An API error occurred"
        assert result["status_code"] == 500
        assert result["type"] == "api_error"

    def test_add_additional_fields_includes_existing(self):
        error = ApiError()
        error.custom_field = "custom_value"
        data = {"existing": "data"}
        result = error._add_additional_fields(data, ["custom_field"])
        assert result["custom_field"] == "custom_value"
        assert result["existing"] == "data"

    def test_add_additional_fields_ignores_nonexistent(self):
        error = ApiError()
        data = {"existing": "data"}
        result = error._add_additional_fields(data, ["nonexistent_field"])
        assert "nonexistent_field" not in result
        assert result["existing"] == "data"

class TestBaseErrorTypes:
    @pytest.mark.parametrize("error_class,base_class,expected_type", [
        (ClientError, ApiError, "client_error"),
        (ServerError, ApiError, "server_error"),
    ])
    def test_error_types(self, error_class, base_class, expected_type):
        error = error_class(message="Test", status_code=400)
        assert error.error_type == expected_type
        assert error.to_dict()["type"] == expected_type
        assert isinstance(error, base_class)

class TestBadRequestError:
    def test_default_configuration(self):
        error = BadRequestError()
        assert error.status_code == 400
        assert "invalid or malformed" in error.message.lower()
        assert error.invalid_fields == []
        assert isinstance(error, ClientError)

    def test_with_invalid_fields(self):
        error = BadRequestError(message="Validation failed", invalid_fields=["email", "password"])
        assert error.invalid_fields == ["email", "password"]
        assert error.message == "Validation failed"

    def test_serialization_includes_invalid_fields(self, bad_request_error):
        result = bad_request_error.to_dict()
        assert result["invalid_fields"] == ["email", "password"]
        assert result["message"] == "Validation failed"
        assert result["status_code"] == 400

    def test_serialization_with_empty_invalid_fields(self):
        error = BadRequestError()
        result = error.to_dict()
        assert result["invalid_fields"] == []

class TestUnauthorizedError:
    def test_default_configuration(self):
        error = UnauthorizedError()
        assert error.status_code == 401
        assert "Authentication credentials" in error.message
        assert isinstance(error, ClientError)

    def test_with_custom_message_and_response(self, sample_response_data):
        error = UnauthorizedError(message="Token expired", response=sample_response_data)
        assert error.message == "Token expired"
        assert error.response == sample_response_data

class TestForbiddenError:
    def test_default_configuration(self):
        error = ForbiddenError()
        assert error.status_code == 403
        assert "permission" in error.message.lower()
        assert isinstance(error, ClientError)

    def test_with_required_permissions(self):
        error = ForbiddenError(message="Admin access required", required_permissions="admin")
        assert error.required_permissions == "admin"
        assert error.message == "Admin access required"

    def test_serialization_includes_required_permissions(self, forbidden_error):
        result = forbidden_error.to_dict()
        assert result["required_permissions"] == "admin"
        assert result["message"] == "Access denied"
        assert result["status_code"] == 403

    def test_serialization_without_required_permissions(self):
        error = ForbiddenError()
        result = error.to_dict()
        assert "required_permissions" not in result or result["required_permissions"] is None

class TestTooManyRequestsError:
    def test_default_configuration(self):
        error = TooManyRequestsError()
        assert error.status_code == 429
        assert "rate limit" in error.message.lower()
        assert isinstance(error, ClientError)

    def test_with_rate_limit_details(self):
        error = TooManyRequestsError(message="Rate limit exceeded", retry_after=60, limit=100)
        assert error.retry_after == 60
        assert error.limit == 100
        assert error.message == "Rate limit exceeded"

    def test_serialization_includes_all_rate_limit_fields(self, rate_limit_error):
        result = rate_limit_error.to_dict()
        assert result["retry_after"] == 60
        assert result["limit"] == 100
        assert result["status_code"] == 429

    def test_serialization_with_partial_fields(self):
        error = TooManyRequestsError(retry_after=30)
        result = error.to_dict()
        assert result["retry_after"] == 30
        assert "limit" not in result or result["limit"] is None

class TestInternalServerError:
    def test_default_configuration(self):
        error = InternalServerError()
        assert error.status_code == 500
        assert "server" in error.message.lower()
        assert isinstance(error, ServerError)

    def test_with_error_id(self):
        error = InternalServerError(message="Database connection failed", error_id="ERR-DB-001")
        assert error.error_id == "ERR-DB-001"
        assert error.message == "Database connection failed"

    def test_serialization_includes_error_id(self, internal_server_error):
        result = internal_server_error.to_dict()
        assert result["error_id"] == "ERR-DB-001"
        assert result["message"] == "Database error"
        assert result["status_code"] == 500

class TestExceptionMapperFromResponse:
    @pytest.mark.parametrize("status_code,expected_class", STATUS_CODE_MAPPING.items())
    def test_creates_correct_error_class(self, status_code, expected_class):
        error = ExceptionMapper.from_response(status_code)
        assert isinstance(error, expected_class)
        assert error.status_code == status_code

    def test_with_custom_message(self):
        error = ExceptionMapper.from_response(400, message="Custom validation error")
        assert error.message == "Custom validation error"
        assert isinstance(error, BadRequestError)

    def test_with_response_data(self, sample_error_response):
        error = ExceptionMapper.from_response(401, response=sample_error_response)
        assert error.response == sample_error_response
        assert isinstance(error, UnauthorizedError)

    def test_with_all_parameters(self, sample_error_response):
        error = ExceptionMapper.from_response(403, message="Access denied", response=sample_error_response)
        assert error.message == "Access denied"
        assert error.response == sample_error_response
        assert isinstance(error, ForbiddenError)

class TestExceptionMapperUnknownStatusCodes:
    def test_unknown_status_code_returns_base_api_error(self):
        error = ExceptionMapper.from_response(418)
        assert isinstance(error, ApiError)
        assert not isinstance(error, (ClientError, ServerError))
        assert error.status_code == 418

    def test_unknown_status_code_with_custom_data(self):
        error = ExceptionMapper.from_response(418, message="I'm a teapot", response={"teapot": True})
        assert error.message == "I'm a teapot"
        assert error.status_code == 418
        assert error.response == {"teapot": True}

class TestExceptionMapperRaiseForStatus:
    @pytest.mark.parametrize("status_code,expected_error", STATUS_CODE_MAPPING.items())
    def test_raises_correct_error_type(self, status_code, expected_error):
        with pytest.raises(expected_error):
            ExceptionMapper.raise_for_status(status_code)

    def test_raises_with_custom_message(self):
        with pytest.raises(BadRequestError) as exc_info:
            ExceptionMapper.raise_for_status(400, message="Invalid request")
        assert exc_info.value.message == "Invalid request"

    @pytest.mark.parametrize("status_code", ERROR_STATUS_CODES)
    def test_raises_for_unknown_error_codes(self, status_code):
        with pytest.raises(ApiError):
            ExceptionMapper.raise_for_status(status_code)

    @pytest.mark.parametrize("status_code", SUCCESS_STATUS_CODES)
    def test_does_not_raise_for_success_codes(self, status_code):
        ExceptionMapper.raise_for_status(status_code)

class TestExceptionMapperGetErrorClass:
    @pytest.mark.parametrize("status_code,expected_class", STATUS_CODE_MAPPING.items())
    def test_returns_correct_error_class(self, status_code, expected_class):
        error_class = ExceptionMapper.get_error_class(status_code)
        assert error_class == expected_class

    def test_returns_base_api_error_for_unknown_codes(self):
        error_class = ExceptionMapper.get_error_class(404)
        assert error_class == ApiError

class TestHandleApiErrorsBasicFunctionality:
    def test_successful_function_execution(self):
        @handle_api_errors()
        def successful_func():
            return "success"
        assert successful_func() == "success"

    def test_with_function_arguments(self):
        @handle_api_errors(default_return=0)
        def add_numbers(a, b):
            if a < 0:
                raise BadRequestError("Negative numbers not allowed")
            return a + b
        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 5) == 0

    def test_with_keyword_arguments(self):
        @handle_api_errors(default_return={})
        def get_user(user_id=None):
            if user_id is None:
                raise BadRequestError("user_id required")
            return {"id": user_id, "name": "Test"}
        assert get_user(user_id=123) == {"id": 123, "name": "Test"}
        assert get_user() == {}

class TestHandleApiErrorsErrorHandling:
    def test_catches_api_error_returns_default(self):
        @handle_api_errors(default_return="error_occurred")
        def failing_func():
            raise BadRequestError("Invalid input")
        assert failing_func() == "error_occurred"

    def test_returns_none_by_default(self):
        @handle_api_errors()
        def failing_func():
            raise UnauthorizedError("No token")
        assert failing_func() is None

    def test_does_not_catch_non_api_errors(self):
        @handle_api_errors()
        def failing_func():
            raise ValueError("Not an API error")
        with pytest.raises(ValueError, match="Not an API error"):
            failing_func()

    @pytest.mark.parametrize("error_class", ALL_API_ERROR_CLASSES)
    def test_catches_all_api_error_subclasses(self, error_class):
        @handle_api_errors(default_return="handled")
        def failing_func():
            raise error_class("Error")
        assert failing_func() == "handled"

class TestHandleApiErrorsLogging:
    def test_logs_errors_by_default(self, capsys):
        @handle_api_errors()
        def failing_func():
            raise ForbiddenError("Access denied")
        failing_func()
        captured = capsys.readouterr()
        assert "ForbiddenError" in captured.out
        assert "failing_func" in captured.out
        assert "Access denied" in captured.out

    def test_disables_logging_when_log_errors_false(self, capsys):
        @handle_api_errors(log_errors=False)
        def failing_func():
            raise BadRequestError("Bad input")
        failing_func()
        captured = capsys.readouterr()
        assert captured.out == ""

class TestHandleApiErrorsEdgeCases:
    def test_multiple_errors_in_sequence(self):
        call_count = 0
        
        @handle_api_errors(default_return="handled")
        def multi_error_func(should_fail):
            nonlocal call_count
            call_count += 1
            if should_fail:
                if call_count == 1:
                    raise BadRequestError()
                else:
                    raise InternalServerError()
            return "success"
        
        assert multi_error_func(True) == "handled"
        assert multi_error_func(True) == "handled"
        assert multi_error_func(False) == "success"

    @pytest.mark.parametrize("default_return,expected", [
        ([], []),
        ({}, {}),
        (False, False)
    ])
    def test_with_different_default_return_types(self, default_return, expected):
        @handle_api_errors(default_return=default_return)
        def failing_func():
            raise ApiError()
        assert failing_func() == expected

    def test_nested_function_calls(self):
        @handle_api_errors(default_return="outer_error")
        def outer_func():
            return inner_func()
        
        @handle_api_errors(default_return="inner_error")
        def inner_func():
            raise BadRequestError("Inner error")
        
        assert outer_func() == "inner_error"

class TestErrorInheritance:
    @pytest.mark.parametrize("error_class,expected_parents", [
        (BadRequestError, (ClientError, ApiError, Exception)),
        (UnauthorizedError, (ClientError, ApiError, Exception)),
        (ForbiddenError, (ClientError, ApiError, Exception)),
        (TooManyRequestsError, (ClientError, ApiError, Exception)),
        (InternalServerError, (ServerError, ApiError, Exception)),
        (ClientError, (ApiError, Exception)),
        (ServerError, (ApiError, Exception)),
        (ApiError, (Exception,)),
    ])
    def test_inheritance_chain(self, error_class, expected_parents):
        for parent in expected_parents:
            assert issubclass(error_class, parent)

class TestApiErrorEdgeCases:
    def test_empty_string_message_uses_default(self):
        error = ApiError(message="")
        assert error.message == "An API error occurred"

    def test_zero_status_code_uses_default(self):
        error = ApiError(status_code=0)
        assert error.status_code == 500

    def test_none_values_in_initialization(self):
        error = ApiError(message=None, status_code=None, response=None, error_code=None)
        assert error.response is None

class TestRateLimitErrorEdgeCases:
    @pytest.mark.parametrize("retry_after,limit", [
        (-1, 100),
        (30, 0),
        (999999, 999999999),
    ])
    def test_unusual_values(self, retry_after, limit):
        error = TooManyRequestsError(retry_after=retry_after, limit=limit)
        assert error.retry_after == retry_after
        assert error.limit == limit

class TestExceptionMapperEdgeCases:
    @pytest.mark.parametrize("status_code,should_raise", [
        (399, False),
        (400, True),
        (499, True),
        (500, True),
        (599, True),
        (9999, True),
    ])
    def test_boundary_status_codes(self, status_code, should_raise):
        if should_raise:
            with pytest.raises(Exception):
                ExceptionMapper.raise_for_status(status_code)
        else:
            ExceptionMapper.raise_for_status(status_code)

class TestInvalidFieldsEdgeCases:
    @pytest.mark.parametrize("invalid_fields", [
        ["email"],
        [f"field_{i}" for i in range(100)],
        ["email", "email", "password"],
    ])
    def test_various_invalid_fields(self, invalid_fields):
        error = BadRequestError(invalid_fields=invalid_fields)
        assert error.invalid_fields == invalid_fields

class TestSerializationEdgeCases:
    def test_to_dict_with_none_response(self):
        error = ApiError(response=None)
        result = error.to_dict()
        assert result["response"] is None

    def test_to_dict_with_complex_response(self):
        complex_response = {
            "errors": [
                {"field": "email", "message": "Invalid"},
                {"field": "password", "message": "Too short"}
            ],
            "metadata": {
                "timestamp": 1234567890,
                "request_id": "abc-123"
            }
        }
        error = ApiError(response=complex_response)
        result = error.to_dict()
        assert result["response"] == complex_response

    def test_add_additional_fields_with_empty_list(self):
        error = ApiError()
        data = {"existing": "data"}
        result = error._add_additional_fields(data, [])
        assert result == {"existing": "data"}