import asyncio
import logging
import unittest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.connection import ConnectionHandler
import src.connection as connection_module


def _run(coro):
    return asyncio.run(coro)


def _response(status_code, json_body=None, text='', headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    resp.json.return_value = {} if json_body is None else json_body
    return resp


class ConnectionHandlerAuthTests(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        self.config.base_headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': 'Bearer org-pat',
        }
        self.config.base_url = 'https://api.github.com'
        self.config_patcher = patch('src.connection.Config', return_value=self.config)
        self.ConfigMock = self.config_patcher.start()
        # Plain function reference: staticmethod objects are not callable on Python < 3.10.
        self.ConfigMock.generate_auth_header = Config.generate_auth_header
        self.addCleanup(self.config_patcher.stop)
        connection_module._locked_out_tokens.clear()
        self.addCleanup(connection_module._locked_out_tokens.clear)

    def test_instance_pat_does_not_mutate_shared_config_headers(self):
        handler = ConnectionHandler(pat='member-token')

        self.assertEqual(handler.headers['Authorization'], 'Bearer member-token')
        self.assertEqual(self.config.base_headers['Authorization'], 'Bearer org-pat')

    def test_graphql_member_token_does_not_stick_on_handler(self):
        handler = ConnectionHandler()
        graphql_resp = _response(200, json_body={'data': {'ok': True}})

        with patch('src.connection.requests.post', return_value=graphql_resp) as post:
            _run(handler.post_graphql('query Q { viewer { login } }', {}, 'member-token'))

        sent_headers = post.call_args.kwargs['headers']
        self.assertEqual(sent_headers['Authorization'], 'Bearer member-token')
        self.assertEqual(handler.headers['Authorization'], 'Bearer org-pat')
        self.assertEqual(self.config.base_headers['Authorization'], 'Bearer org-pat')

    def test_tls_verification_is_not_disabled(self):
        handler = ConnectionHandler()
        ok = _response(200, json_body={'ok': True})

        with patch('src.connection.requests.get', return_value=ok) as get:
            _run(handler.get('/user'))

        self.assertNotIn('verify', get.call_args.kwargs)

    def test_expired_token_is_not_retried_as_rate_limit(self):
        handler = ConnectionHandler()
        expired = _response(
            401,
            json_body={'message': 'Token expired'},
            text='{"message":"Token expired"}',
        )

        with patch('src.connection.requests.get', return_value=expired) as get, \
             patch.object(handler, '_ConnectionHandler__validate_rate_limit') as rate_limit, \
             self.assertLogs(level=logging.ERROR) as logs:
            result = _run(handler.get('/user'))

        self.assertEqual(get.call_count, 1)
        rate_limit.assert_not_called()
        self.assertEqual(result, {'message': 'Token expired'})
        self.assertTrue(any('expired' in message.lower() for message in logs.output))

    def test_invalid_credentials_are_not_retried(self):
        handler = ConnectionHandler()
        bad = _response(
            401,
            json_body={'message': 'Bad credentials'},
            text='{"message":"Bad credentials"}',
        )

        with patch('src.connection.requests.post', return_value=bad) as post, \
             patch.object(handler, '_ConnectionHandler__validate_rate_limit') as rate_limit:
            _run(handler.post('/orgs/example/invitations', {'invitee_id': 1}))

        self.assertEqual(post.call_count, 1)
        rate_limit.assert_not_called()

    def test_failed_token_is_locked_out_from_reuse(self):
        handler = ConnectionHandler()
        expired = _response(
            401,
            json_body={'message': 'Token expired'},
            text='{"message":"Token expired"}',
        )

        with patch('src.connection.requests.get', return_value=expired) as get:
            _run(handler.get('/user'))
            with self.assertLogs(level=logging.ERROR) as logs:
                result = _run(handler.get('/user/repos'))

        # Only the first request reaches the API; the reuse is refused locally.
        self.assertEqual(get.call_count, 1)
        self.assertEqual(result, {})
        self.assertTrue(any('locked out' in message for message in logs.output))

    def test_lockout_applies_across_handlers_and_methods(self):
        first = ConnectionHandler()
        expired = _response(401, text='{"message":"Token expired"}')

        with patch('src.connection.requests.get', return_value=expired):
            _run(first.get('/user'))

        second = ConnectionHandler()
        with patch('src.connection.requests.post') as post, \
             patch('src.connection.requests.put') as put:
            _run(second.post('/repos', {'name': 'x'}))
            _run(second.put('/repos/x', {'private': True}))

        post.assert_not_called()
        put.assert_not_called()

    def test_graphql_lockout_does_not_affect_org_pat(self):
        handler = ConnectionHandler()
        expired = _response(401, text='{"message":"Token expired"}')
        ok = _response(200, json_body={'ok': True})

        with patch('src.connection.requests.post', return_value=expired):
            _run(handler.post_graphql('query Q { viewer { login } }', {}, 'member-token'))

        with patch('src.connection.requests.post', return_value=ok) as post_rest, \
             patch('src.connection.requests.get', return_value=ok) as get_rest:
            # The expired member token is refused before any HTTP call.
            _run(handler.post_graphql('query Q { viewer { login } }', {}, 'member-token'))
            post_rest.assert_not_called()
            # The org PAT is unaffected and still works.
            result = _run(handler.get('/user'))

        self.assertEqual(get_rest.call_count, 1)
        self.assertEqual(result, {'ok': True})

    def test_secondary_throttling_sleeps_retry_after_seconds(self):
        handler = ConnectionHandler()
        throttled = _response(
            403,
            text='secondary rate limit',
            headers={
                'X-RateLimit-Remaining': '10',
                'Retry-After': '7',
            },
        )
        ok = _response(200, json_body={'ok': True})

        with patch('src.connection.requests.get', side_effect=[throttled, ok]), \
             patch('src.connection.time.sleep') as sleep:
            result = _run(handler.get('/rate_limit'))

        sleep.assert_called_once_with(7)
        self.assertEqual(result, {'ok': True})


if __name__ == '__main__':
    unittest.main()
