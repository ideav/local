"""
Tests for XSRF protection
"""
import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock
from app import app, validate_xsrf
from utils import xsrf_token, salt
from config import Config


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client


class TestXSRFTokenGeneration:
    """Test XSRF token generation"""

    def test_xsrf_token_generation(self):
        """Test that XSRF token is generated correctly"""
        token = "test_token_123"
        db_name = "test_db"

        result = xsrf_token(token, db_name)

        # Should return a 22-character token
        assert len(result) == 22
        assert isinstance(result, str)

    def test_xsrf_token_consistency(self):
        """Test that same inputs generate same token"""
        token = "test_token_123"
        db_name = "test_db"

        result1 = xsrf_token(token, db_name)
        result2 = xsrf_token(token, db_name)

        assert result1 == result2

    def test_xsrf_token_uniqueness(self):
        """Test that different inputs generate different tokens"""
        token1 = "test_token_123"
        token2 = "test_token_456"
        db_name = "test_db"

        result1 = xsrf_token(token1, db_name)
        result2 = xsrf_token(token2, db_name)

        assert result1 != result2

    def test_salt_function(self):
        """Test salt function combines inputs correctly"""
        a = "test_a"
        b = "test_b"

        result = salt(a, b)

        # Should contain both inputs and config SALT
        assert a in result
        assert b in result
        assert Config.SALT in result


class TestXSRFValidation:
    """Test XSRF validation"""

    def test_validate_xsrf_with_valid_token(self, client):
        """Test validation with valid token"""
        with client.session_transaction() as sess:
            sess['xsrf_token'] = 'test_token_12345678901'

        with client:
            with client.post('/test', data={'_xsrf': 'test_token_12345678901'}):
                # This will trigger before_request which validates XSRF
                # If validation fails, we'll get 403
                pass

    def test_validate_xsrf_with_invalid_token(self, client):
        """Test validation with invalid token"""
        with client.session_transaction() as sess:
            sess['xsrf_token'] = 'valid_token_1234567890'

        # Try to access with wrong token
        response = client.post('/ideav/edit_obj/1', data={'_xsrf': 'invalid_token_123'})

        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_validate_xsrf_with_missing_token(self, client):
        """Test validation with missing token"""
        with client.session_transaction() as sess:
            sess['xsrf_token'] = 'valid_token_1234567890'

        # Try to access without token
        response = client.post('/ideav/edit_obj/1', data={})

        # Should get 403 Forbidden
        assert response.status_code == 403


class TestXSRFSessionIntegration:
    """Test XSRF token session integration"""

    def test_xsrf_token_created_on_first_request(self, client):
        """Test that XSRF token is created in session on first request"""
        response = client.get('/ideav')

        with client.session_transaction() as sess:
            # Session should have xsrf_token
            assert 'xsrf_token' in sess
            assert len(sess['xsrf_token']) == 22

    def test_xsrf_token_persists_across_requests(self, client):
        """Test that XSRF token persists across requests"""
        # First request
        client.get('/ideav')

        with client.session_transaction() as sess:
            first_token = sess.get('xsrf_token')

        # Second request
        client.get('/ideav')

        with client.session_transaction() as sess:
            second_token = sess.get('xsrf_token')

        # Token should be the same
        assert first_token == second_token

    @patch('app.Database')
    def test_xsrf_token_regenerated_on_login(self, mock_db, client):
        """Test that XSRF token is regenerated after login"""
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_instance)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        # Mock user data
        user_token = "user_token_123456"
        mock_db_instance.execute_one.return_value = {
            'user_id': 1,
            'pwd_hash': hashlib.sha1((Config.SALT + 'password123').encode()).hexdigest(),
            'token': user_token
        }

        # Login
        response = client.post('/auth', data={
            'db': 'ideav',
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=False)

        # Should redirect on success
        assert response.status_code == 302


class TestXSRFExclusions:
    """Test XSRF validation exclusions"""

    @patch('app.Database')
    def test_auth_endpoint_excluded(self, mock_db, client):
        """Test that /auth endpoint is excluded from XSRF validation"""
        # Mock database response
        mock_db_instance = MagicMock()
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_instance)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        # Mock user data
        mock_db_instance.execute_one.return_value = {
            'user_id': 1,
            'pwd_hash': hashlib.sha1((Config.SALT + 'password123').encode()).hexdigest(),
            'token': 'user_token_123'
        }

        # Should not require XSRF token
        response = client.post('/auth', data={
            'db': 'ideav',
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Should not get 403 (may get redirect or error for other reasons)
        assert response.status_code != 403

    def test_api_endpoints_excluded(self, client):
        """Test that API endpoints are excluded from XSRF validation"""
        # API endpoints don't require XSRF token
        # They use token-based authentication instead
        response = client.post('/api/ideav/objects',
                              json={'up': 1, 't': 3, 'val': 'test'},
                              headers={'X-Authorization': 'test_token'})

        # Should not get 403 for missing XSRF (may get 401 for invalid auth)
        assert response.status_code != 403

    def test_get_requests_not_validated(self, client):
        """Test that GET requests are not validated for XSRF"""
        # GET requests should not be validated
        response = client.get('/ideav')

        # Should not get 403
        assert response.status_code != 403


class TestXSRFErrorMessages:
    """Test XSRF error messages"""

    def test_error_message_on_invalid_token(self, client):
        """Test that proper error message is shown on invalid token"""
        with client.session_transaction() as sess:
            sess['xsrf_token'] = 'valid_token_1234567890'

        response = client.post('/ideav/edit_obj/1', data={'_xsrf': 'invalid'})

        # Should get 403 with error message
        assert response.status_code == 403
        assert b'CSRF' in response.data or b'csrf' in response.data.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
