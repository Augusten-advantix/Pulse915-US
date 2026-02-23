"""
Schwab OAuth 2.0 Authentication Module
Handles authorization code flow and access token management.
"""

import os
import json
import time
import requests
import webbrowser
from urllib.parse import urlencode
from datetime import datetime, timedelta
from dotenv import load_dotenv, set_key
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Load environment variables
load_dotenv()

class SchwabAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth 2.0 authorization code."""
    
    auth_code = None
    
    def do_GET(self):
        """Handle the redirect callback from Schwab OAuth."""
        query_params = {}
        if '?' in self.path:
            query_string = self.path.split('?')[1]
            for param in query_string.split('&'):
                key, value = param.split('=', 1)
                query_params[key] = value
        
        if 'code' in query_params:
            SchwabAuthHandler.auth_code = query_params['code']
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to your terminal.</p>
                <p style="color: green;">Authorization code received.</p>
            </body>
            </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Authorization Failed</h1>
                <p>No authorization code received.</p>
            </body>
            </html>
            """)
    
    def log_message(self, format, *args):
        """Suppress HTTP server logging."""
        pass


class SchwabOAuth2:
    """Handles OAuth 2.0 authentication with Charles Schwab API."""
    
    # Schwab OAuth endpoints
    # NOTE: Check https://developer.schwab.com/ for current endpoints
    AUTH_URL = "https://api.schwab.com/v1/oauth/authorize"
    TOKEN_URL = "https://api.schwab.com/v1/oauth/token"
    
    def __init__(self):
        """Initialize Schwab OAuth client."""
        self.client_id = os.getenv('SCHWAB_CLIENT_ID')
        self.client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'http://localhost:8888/callback')
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET must be set in .env file"
            )
    
    def get_authorization_code(self):
        """
        Initiate OAuth 2.0 authorization code flow.
        Opens browser for user to authorize, listens for callback.
        """
        print("Starting OAuth 2.0 authorization flow...")
        
        # Build authorization URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'PlaceTrades AccountAccess MoveMoney'
        }
        
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        
        print(f"\nOpening browser for authorization...")
        print(f"Authorization URL: {auth_url}\n")
        
        # Start local HTTP server to capture callback
        server = HTTPServer(('localhost', 8888), SchwabAuthHandler)
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback (with timeout)
        print("Waiting for authorization callback (timeout: 5 minutes)...")
        timeout = time.time() + 300  # 5 minute timeout
        
        while SchwabAuthHandler.auth_code is None and time.time() < timeout:
            server.handle_request()
        
        if SchwabAuthHandler.auth_code is None:
            raise TimeoutError("Authorization code not received within timeout period")
        
        auth_code = SchwabAuthHandler.auth_code
        print(f"✓ Authorization code received: {auth_code[:20]}...")
        
        return auth_code
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token."""
        print("\nExchanging authorization code for access token...")
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_response = response.json()
            self.access_token = token_response.get('access_token')
            self.refresh_token = token_response.get('refresh_token')
            
            # Calculate token expiration
            expires_in = token_response.get('expires_in', 1800)  # Default 30 minutes
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"✓ Access token received")
            print(f"✓ Token expires at: {self.token_expires_at}")
            
            # Save to .env file
            self._save_tokens()
            
            return token_response
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error exchanging code for token: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        print("\nRefreshing access token...")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_response = response.json()
            self.access_token = token_response.get('access_token')
            self.refresh_token = token_response.get('refresh_token', self.refresh_token)
            
            # Calculate token expiration
            expires_in = token_response.get('expires_in', 1800)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"✓ Token refreshed successfully")
            print(f"✓ New token expires at: {self.token_expires_at}")
            
            # Save updated tokens
            self._save_tokens()
            
            return token_response
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error refreshing token: {e}")
            raise
    
    def _save_tokens(self):
        """Save tokens to .env file for later use."""
        env_file = '.env'
        
        # Add or update tokens in .env
        set_key(env_file, 'SCHWAB_ACCESS_TOKEN', self.access_token)
        set_key(env_file, 'SCHWAB_REFRESH_TOKEN', self.refresh_token)
        set_key(env_file, 'SCHWAB_TOKEN_EXPIRES_AT', self.token_expires_at.isoformat())
        
        print(f"✓ Tokens saved to {env_file}")
    
    def load_tokens_from_env(self):
        """Load previously saved tokens from .env file."""
        self.access_token = os.getenv('SCHWAB_ACCESS_TOKEN', '').strip() or None
        self.refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN', '').strip() or None
        
        expires_at_str = os.getenv('SCHWAB_TOKEN_EXPIRES_AT', '').strip()
        if expires_at_str:
            try:
                self.token_expires_at = datetime.fromisoformat(expires_at_str)
            except ValueError:
                self.token_expires_at = None
        
        return self.access_token is not None
    
    def ensure_valid_token(self):
        """Ensure we have a valid access token, refresh if needed."""
        # Try to load from env first
        if self.load_tokens_from_env():
            print("✓ Loaded tokens from .env")
            
            # Check if token is expired or about to expire (within 5 minutes)
            if self.token_expires_at and datetime.now() >= self.token_expires_at - timedelta(minutes=5):
                print("Token expired or expiring soon, refreshing...")
                self.refresh_access_token()
            
            return self.access_token
        
        # Otherwise, initiate full OAuth flow
        print("No valid tokens found in .env, initiating OAuth flow...")
        auth_code = self.get_authorization_code()
        self.exchange_code_for_token(auth_code)
        
        return self.access_token
    
    def get_auth_headers(self):
        """Get HTTP headers with authentication."""
        self.ensure_valid_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }


def initialize_schwab_oauth():
    """Initialize and authenticate with Schwab API."""
    oauth = SchwabOAuth2()
    token = oauth.ensure_valid_token()
    
    if token:
        print("\n✓ Successfully authenticated with Schwab API!")
        return oauth
    else:
        raise Exception("Failed to obtain authentication token")


if __name__ == '__main__':
    # Test the OAuth flow
    try:
        oauth = initialize_schwab_oauth()
        print("\nAuthentication successful!")
        print(f"Access Token: {oauth.access_token[:20]}...")
        print(f"Refresh Token: {oauth.refresh_token[:20]}...")
        print(f"Expires at: {oauth.token_expires_at}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
