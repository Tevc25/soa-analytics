import jwt
import os
from typing import Dict, Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """
        Verifies JWT token and returns payload if valid.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> Dict:
        """
        Validates JWT token from Authorization header and returns user info.
        Raises HTTPException if token is invalid.
        """
        token = credentials.credentials
        payload = self.verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload

    def validate_user_id(self, token_user_id: str, path_user_id: str):
        """
        Validates that the user_id from token matches the user_id in the path.
        Raises HTTPException if they don't match.
        """
        if token_user_id != path_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )

auth_service = AuthService()

