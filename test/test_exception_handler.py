import pytest
from src.exception_handler import ApiError, ClientError, ServerError, BadRequestError, UnauthorizedError, ForbiddenError, TooManyRequestsError, InternalServerError, ExceptionMapper, handle_api_errors


class TestApiError:
    """Test the base ApiError class"""
    
    def test_default_initialization(self):
        error = ApiError()
        assert error.message == "An API error occurred"
        assert error.status_code == 500
        assert error.response is None
        assert error.error_code == "ApiError"
    
    def test_custom_message(self):
        error = ApiError(message="Custom error")
        assert error.message == "Custom error"
        assert str(error) == "[500] Custom error"
    
    def test_custom_status_code(self):
        error = ApiError(status_code=404)
        assert error.status_code == 404
    
    def test_with_response(self):
        response_data = {"detail": "Not found"}
        error = ApiError(response=response_data)
        assert error.response == response_data
    
    def test_custom_error_code(self):
        error = ApiError(error_code="CUSTOM_ERROR")
        assert error.error_code == "CUSTOM_ERROR"
    
    def test_str_representation(self):
        error = ApiError(message="Test error", status_code=404)
        assert str(error) == "[404] Test error"
    
    def test_repr_representation(self):
        error = ApiError(message="Test error", status_code=404)
        assert repr(error) == "ApiError(status_code=404, message=Test error)"
    
    def test_to_dict(self):
        error = ApiError(
            message="Test error",
            status_code=404,
            response={"data": "test"}
        )
        result = error.to_dict()
        
        assert result["message"] == "Test error"
        assert result["status_code"] == 404
        assert result["response"] == {"data": "test"}
        assert result["type"] == "api_error"
    
    def test_add_additional_fields(self):
        error = ApiError()
        error.custom_field = "custom_value"
        data = {"existing": "data"}
        
        result = error._add_additional_fields(data, ["custom_field", "nonexistent"])
        
        assert result["custom_field"] == "custom_value"
        assert "nonexistent" not in result
        assert result["existing"] == "data"


class TestClientError:
    """Test ClientError class"""
    
    def test_error_type(self):
        error = ClientError()
        assert error.error_type == "client_error"
        assert error.to_dict()["type"] == "client_error"
    
    def test_inherits_from_api_error(self):
        error = ClientError(message="Client error", status_code=400)
        assert isinstance(error, ApiError)
        assert error.message == "Client error"
        assert error.status_code == 400


class TestServerError:
    """Test ServerError class"""
    
    def test_error_type(self):
        error = ServerError()
        assert error.error_type == "server_error"
        assert error.to_dict()["type"] == "server_error"
    
    def test_inherits_from_api_error(self):
        error = ServerError(message="Server error", status_code=503)
        assert isinstance(error, ApiError)


class TestBadRequestError:
    """Test BadRequestError class"""
    
    def test_default_message_and_status_code(self):
        error = BadRequestError()
        assert error.status_code == 400
        assert "invalid or malformed" in error.message
        assert error.invalid_fields == []
    
    def test_custom_message(self):
        error = BadRequestError(message="Invalid input")
        assert error.message == "Invalid input"
    
    def test_with_invalid_fields(self):
        error = BadRequestError(invalid_fields=["email", "password"])
        assert error.invalid_fields == ["email", "password"]
    
    def test_to_dict_includes_invalid_fields(self):
        error = BadRequestError(
            message="Validation failed",
            invalid_fields=["username", "age"]
        )
        result = error.to_dict()
        
        assert result["invalid_fields"] == ["username", "age"]
        assert result["message"] == "Validation failed"
        assert result["status_code"] == 400
    
    def test_to_dict_without_invalid_fields(self):
        error = BadRequestError()
        result = error.to_dict()
        # Empty list should still be included
        assert result["invalid_fields"] == []


class TestUnauthorizedError:
    """Test UnauthorizedError class"""
    
    def test_default_message_and_status_code(self):
        error = UnauthorizedError()
        assert error.status_code == 401
        assert "Authentication credentials" in error.message
    
    def test_custom_message(self):
        error = UnauthorizedError(message="Invalid token")
        assert error.message == "Invalid token"
    
    def test_with_response(self):
        response_data = {"error": "token_expired"}
        error = UnauthorizedError(response=response_data)
        assert error.response == response_data


class TestForbiddenError:
    """Test ForbiddenError class"""
    
    def test_default_message_and_status_code(self):
        error = ForbiddenError()
        assert error.status_code == 403
        assert "permission" in error.message.lower()
    
    def test_with_required_permissions(self):
        error = ForbiddenError(required_permissions="admin")
        assert error.required_permissions == "admin"
    
    def test_to_dict_includes_required_permissions(self):
        error = ForbiddenError(
            message="Access denied",
            required_permissions="write:users"
        )
        result = error.to_dict()
        
        assert result["required_permissions"] == "write:users"
        assert result["status_code"] == 403
    
    def test_to_dict_without_required_permissions(self):
        error = ForbiddenError()
        result = error.to_dict()
        # None values shouldn't be added
        assert "required_permissions" not in result or result["required_permissions"] is None


class TestTooManyRequestsError:
    """Test TooManyRequestsError class"""
    
    def test_default_message_and_status_code(self):
        error = TooManyRequestsError()
        assert error.status_code == 429
        assert "rate limit" in error.message.lower()
    
    def test_with_retry_after(self):
        error = TooManyRequestsError(retry_after=60)
        assert error.retry_after == 60
    
    def test_with_limit(self):
        error = TooManyRequestsError(limit=100)
        assert error.limit == 100
    
    def test_to_dict_includes_rate_limit_fields(self):
        error = TooManyRequestsError(
            message="Rate limit exceeded",
            retry_after=120,
            limit=1000
        )
        result = error.to_dict()
        
        assert result["retry_after"] == 120
        assert result["limit"] == 1000
        assert result["status_code"] == 429
    
    def test_to_dict_with_partial_fields(self):
        error = TooManyRequestsError(retry_after=30)
        result = error.to_dict()
        
        assert result["retry_after"] == 30
        # None values shouldn't be added by _add_additional_fields
        assert "limit" not in result or result["limit"] is None


class TestInternalServerError:
    """Test InternalServerError class"""
    
    def test_default_message_and_status_code(self):
        error = InternalServerError()
        assert error.status_code == 500
        assert "server" in error.message.lower()
    
    def test_with_error_id(self):
        error = InternalServerError(error_id="ERR-123456")
        assert error.error_id == "ERR-123456"
    
    def test_to_dict_includes_error_id(self):
        error = InternalServerError(
            message="Database connection failed",
            error_id="ERR-DB-001"
        )
        result = error.to_dict()
        
        assert result["error_id"] == "ERR-DB-001"
        assert result["status_code"] == 500


class TestExceptionMapper:
    """Test ExceptionMapper class"""
    
    @pytest.mark.parametrize("status_code,expected_class", [
        (400, BadRequestError),
        (401, UnauthorizedError),
        (403, ForbiddenError),
        (429, TooManyRequestsError),
        (500, InternalServerError),
    ])
    def test_from_response_creates_correct_error_class(self, status_code, expected_class):
        error = ExceptionMapper.from_response(status_code)
        assert isinstance(error, expected_class)
        assert error.status_code == status_code
    
    def test_from_response_with_custom_message(self):
        error = ExceptionMapper.from_response(400, message="Custom bad request")
        assert error.message == "Custom bad request"
        assert isinstance(error, BadRequestError)
    
    def test_from_response_with_response_data(self):
        response_data = {"detail": "Error details"}
        error = ExceptionMapper.from_response(401, response=response_data)
        assert error.response == response_data
        assert isinstance(error, UnauthorizedError)
    
    def test_from_response_unknown_status_code(self):
        error = ExceptionMapper.from_response(418)  # I'm a teapot
        assert isinstance(error, ApiError)
        assert not isinstance(error, (ClientError, ServerError))
        assert error.status_code == 418
    
    def test_from_response_unknown_with_message(self):
        error = ExceptionMapper.from_response(
            418,
            message="I'm a teapot",
            response={"teapot": True}
        )
        assert error.message == "I'm a teapot"
        assert error.status_code == 418
        assert error.response == {"teapot": True}
    
    def test_raise_for_status_raises_error(self):
        with pytest.raises(BadRequestError):
            ExceptionMapper.raise_for_status(400, message="Bad request")
    
    def test_raise_for_status_with_different_errors(self):
        with pytest.raises(UnauthorizedError):
            ExceptionMapper.raise_for_status(401)
        
        with pytest.raises(ForbiddenError):
            ExceptionMapper.raise_for_status(403)
        
        with pytest.raises(TooManyRequestsError):
            ExceptionMapper.raise_for_status(429)
        
        with pytest.raises(InternalServerError):
            ExceptionMapper.raise_for_status(500)
    
    def test_raise_for_status_does_not_raise_for_success(self):
        # Should not raise for 2xx and 3xx status codes
        ExceptionMapper.raise_for_status(200)
        ExceptionMapper.raise_for_status(201)
        ExceptionMapper.raise_for_status(301)
        ExceptionMapper.raise_for_status(399)
    
    def test_raise_for_status_raises_for_all_4xx_5xx(self):
        with pytest.raises(ApiError):
            ExceptionMapper.raise_for_status(404)
        
        with pytest.raises(ApiError):
            ExceptionMapper.raise_for_status(503)
    
    @pytest.mark.parametrize("status_code,expected_class", [
        (400, BadRequestError),
        (401, UnauthorizedError),
        (403, ForbiddenError),
        (429, TooManyRequestsError),
        (500, InternalServerError),
        (404, ApiError),  # Unknown code returns base class
    ])
    def test_get_error_class(self, status_code, expected_class):
        error_class = ExceptionMapper.get_error_class(status_code)
        assert error_class == expected_class


class TestHandleApiErrorsDecorator:
    """Test the handle_api_errors decorator"""
    
    def test_successful_function_execution(self):
        @handle_api_errors()
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_catches_api_error_returns_default(self):
        @handle_api_errors(default_return="error_occurred")
        def failing_func():
            raise BadRequestError("Invalid input")
        
        result = failing_func()
        assert result == "error_occurred"
    
    def test_catches_api_error_returns_none_by_default(self):
        @handle_api_errors()
        def failing_func():
            raise UnauthorizedError("No token")
        
        result = failing_func()
        assert result is None
    
    def test_logs_errors_by_default(self, capsys):
        @handle_api_errors()
        def failing_func():
            raise ForbiddenError("Access denied")
        
        failing_func()
        captured = capsys.readouterr()
        
        assert "ForbiddenError" in captured.out
        assert "failing_func" in captured.out
        assert "Access denied" in captured.out
        assert "Response:" in captured.out
    
    def test_disables_logging_when_log_errors_false(self, capsys):
        @handle_api_errors(log_errors=False)
        def failing_func():
            raise BadRequestError("Bad input")
        
        failing_func()
        captured = capsys.readouterr()
        
        assert captured.out == ""
    
    def test_does_not_catch_non_api_errors(self):
        @handle_api_errors()
        def failing_func():
            raise ValueError("Not an API error")
        
        with pytest.raises(ValueError):
            failing_func()
    
    def test_with_function_arguments(self):
        @handle_api_errors(default_return=0)
        def add_numbers(a, b):
            if a < 0:
                raise BadRequestError("Negative numbers not allowed")
            return a + b
        
        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 5) == 0
    
    def test_with_kwargs(self):
        @handle_api_errors(default_return={})
        def get_user(user_id=None):
            if user_id is None:
                raise BadRequestError("user_id required")
            return {"id": user_id, "name": "Test"}
        
        assert get_user(user_id=123) == {"id": 123, "name": "Test"}
        assert get_user() == {}
    
    def test_preserves_error_details_in_log(self, capsys):
        @handle_api_errors()
        def rate_limited_func():
            raise TooManyRequestsError(
                "Too many requests",
                retry_after=60,
                limit=100
            )
        
        rate_limited_func()
        captured = capsys.readouterr()
        
        # Check that to_dict() output is logged
        assert "retry_after" in captured.out
        assert "60" in captured.out


class TestErrorInheritanceChain:
    """Test the inheritance relationships"""
    
    def test_client_errors_inherit_correctly(self):
        assert issubclass(BadRequestError, ClientError)
        assert issubclass(UnauthorizedError, ClientError)
        assert issubclass(ForbiddenError, ClientError)
        assert issubclass(TooManyRequestsError, ClientError)
    
    def test_server_errors_inherit_correctly(self):
        assert issubclass(InternalServerError, ServerError)
    
    def test_all_inherit_from_api_error(self):
        errors = [
            ClientError, ServerError, BadRequestError,
            UnauthorizedError, ForbiddenError,
            TooManyRequestsError, InternalServerError
        ]
        for error_class in errors:
            assert issubclass(error_class, ApiError)
    
    def test_all_inherit_from_exception(self):
        errors = [
            ApiError, ClientError, ServerError, BadRequestError,
            UnauthorizedError, ForbiddenError,
            TooManyRequestsError, InternalServerError
        ]
        for error_class in errors:
            assert issubclass(error_class, Exception)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_string_message(self):
        error = ApiError(message="")
        # Empty string is still truthy for message parameter
        assert error.message == "An API error occurred"
    
    def test_zero_status_code(self):
        error = ApiError(status_code=0)
        assert error.status_code == 500
    
    def test_very_large_status_code(self):
        error = ExceptionMapper.from_response(999)
        assert error.status_code == 999
        assert isinstance(error, ApiError)
    
    def test_negative_retry_after(self):
        error = TooManyRequestsError(retry_after=-1)
        assert error.retry_after == -1
    
    def test_multiple_errors_in_decorator(self):
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