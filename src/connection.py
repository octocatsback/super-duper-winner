import logging, requests, time
from src.config import Config
from datetime import datetime

# Authorization header values that failed authentication (expired, revoked, or
# invalid tokens). Shared across all handlers so a bad token is locked out of
# any reuse for the remainder of the process.
_locked_out_tokens = set()

class ConnectionHandler:
    
    def __init__(self, pat = None, config_file = None):
        self.config = Config() if config_file is None else Config(config_file)
        # Copy headers so a per-request or per-member token cannot leak into
        # Config.base_headers or other ConnectionHandler instances.
        self.headers = dict(self.config.base_headers)
        self.base_url = self.config.base_url
        if pat is not None:
            self.headers['Authorization'] = Config.generate_auth_header(pat)

    def _request_headers(self, token=None):
        headers = dict(self.headers)
        if token is not None:
            headers['Authorization'] = Config.generate_auth_header(token)
        return headers

    def _is_auth_token_failure(self, resp):
        return resp.status_code == 401

    def _is_locked_out(self, headers):
        auth = headers.get('Authorization')
        return auth is not None and auth in _locked_out_tokens

    def _lock_out(self, headers):
        auth = headers.get('Authorization')
        if auth is not None:
            _locked_out_tokens.add(auth)

    def _refuse_locked_out(self, method, endpoint):
        logging.error(
            f'Refusing {method} {endpoint}: this token previously failed '
            f'authentication and is locked out from reuse.'
        )
        return {}

    def _log_auth_token_failure(self, method, endpoint, resp):
        body = (resp.text or '').lower()
        if 'expir' in body:
            reason = 'expired'
        elif 'bad credentials' in body:
            reason = 'invalid or revoked'
        else:
            reason = 'expired, revoked, or invalid'
        logging.error(
            f'Authentication failed ({resp.status_code}) for {method} {endpoint}. '
            f'The GitHub token appears to be {reason}. Message: {resp.text}'
        )

    def _should_retry(self, resp, method, endpoint, headers=None):
        if self._is_auth_token_failure(resp):
            self._log_auth_token_failure(method, endpoint, resp)
            self._lock_out(headers if headers is not None else self.headers)
            return False
        return True

    async def get(self, endpoint):
        if self._is_locked_out(self.headers):
            return self._refuse_locked_out('GET', endpoint)
        resp = requests.get(self.base_url + endpoint, headers=self.headers)
        if resp.status_code != 200:
            logging.warning(f'The response code for the GET endpoint {endpoint} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'GET', endpoint):
                await self.__validate_rate_limit(resp)
                resp = requests.get(self.base_url + endpoint, headers=self.headers)
        try:
            return resp.json()
        except Exception:
            return {}
    
    async def delete(self, endpoint):
        if self._is_locked_out(self.headers):
            self._refuse_locked_out('DELETE', endpoint)
            return
        resp = requests.delete(self.base_url + endpoint, headers=self.headers)
        if resp.status_code != 204:
            logging.debug(f'The response code for the DELETE endpoint {endpoint} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'DELETE', endpoint):
                await self.__validate_rate_limit(resp)
                requests.delete(self.base_url + endpoint, headers=self.headers)
    
    async def post(self, endpoint, json_data):
        if self._is_locked_out(self.headers):
            return self._refuse_locked_out('POST', endpoint)
        resp = requests.post(self.base_url + endpoint, headers=self.headers, json=json_data)
        if resp.status_code not in [200, 201, 202]:
            logging.warning(f'The response code for the POST endpoint {endpoint} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'POST', endpoint):
                await self.__validate_rate_limit(resp)
                resp = requests.post(self.base_url + endpoint, headers=self.headers, json=json_data)
        try:
            return resp.json()
        except Exception:
            return {}
    
    async def post_graphql(self, query, variables, token):
        headers = self._request_headers(token)
        if self._is_locked_out(headers):
            return self._refuse_locked_out('POST', '/graphql')
        payload = {"query": query, "variables": variables}
        resp = requests.post(self.base_url + '/graphql', headers=headers, json=payload)
        if resp.status_code not in [200, 201, 202]:
            logging.warning(f'The response code for the graphql query with the variables {variables} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'POST', '/graphql', headers=headers):
                await self.__validate_rate_limit(resp)
                resp = requests.post(self.base_url + '/graphql', headers=headers, json=payload)
        try:
            return resp.json()
        except Exception:
            return {}
    
    async def put(self, endpoint, json_data):
        if self._is_locked_out(self.headers):
            return self._refuse_locked_out('PUT', endpoint)
        resp = requests.put(self.base_url + endpoint, headers=self.headers, json=json_data)
        if resp.status_code not in [200, 201, 204]:
            logging.warning(f'The response code for the PUT endpoint {endpoint} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'PUT', endpoint):
                await self.__validate_rate_limit(resp)
                resp = requests.put(self.base_url + endpoint, headers=self.headers, json=json_data)
        try:
            return resp.json()
        except Exception:
            return {}
    
    async def patch(self, endpoint, json_data):
        if self._is_locked_out(self.headers):
            return self._refuse_locked_out('PATCH', endpoint)
        resp = requests.patch(self.base_url + endpoint, headers=self.headers, json=json_data)
        if resp.status_code not in [200]:
            logging.warning(f'The response code for the PATCH endpoint {endpoint} is {resp.status_code}. Message: {resp.text}')
            if self._should_retry(resp, 'PATCH', endpoint):
                await self.__validate_rate_limit(resp)
                resp = requests.patch(self.base_url + endpoint, headers=self.headers, json=json_data)
        try:
            return resp.json()
        except Exception:
            return {}

    async def __validate_rate_limit(self, resp):
        remaining_requests = int(resp.headers['X-RateLimit-Remaining']) if 'X-RateLimit-Remaining' in resp.headers else 2
        if remaining_requests <= 1:
            reset = int(resp.headers['X-RateLimit-Reset']) if 'X-RateLimit-Reset' in resp.headers else 0
            now = datetime.timestamp(datetime.now())
            time_to_sleep = max((reset - now) + 1, 1) if reset else 1
            logging.info(f'Primary Throttling: sleeping for {time_to_sleep} seconds')
            time.sleep(time_to_sleep)
        else: 
            retry_after = int(resp.headers['Retry-After']) if 'Retry-After' in resp.headers else 0
            if retry_after > 0:
                logging.info(f'Secondary Throttling: sleeping for {retry_after} seconds')
                time.sleep(retry_after)
