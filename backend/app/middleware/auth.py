from jwt.exceptions import ExpiredSignatureError  
from fastapi.responses import JSONResponse
from fastapi import Request 
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.jwt import decode_jwt
from app.core.exceptions import JWTTokenDecodeError
from app.core.logger import logger

PUBLIC_ROUTES = {
    "/auth/login",
    "/auth/signup",
    "/auth.html",
    "/",
    "/docs",
    "/openapi.json",  
    "/redoc",
    "/index.html",       
    "/css/style.css", 
    "/js/pages.js",
    "/js/core.js",
    "/image/fav.png"
}



class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request: Request, call_next):
        if request.url.path in PUBLIC_ROUTES:
            return await call_next(request)

        token = request.cookies.get("access_token")
        
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        try:
            payload = decode_jwt(token)
            request.state.user_id = int(payload.get("sub"))
            request.state.email = payload.get("email")
            return await call_next(request)
            
        except JWTTokenDecodeError as e:
            if isinstance(e.__cause__, ExpiredSignatureError):
                logger.info(f"Token expired | path: {request.url.path}")
                return JSONResponse(status_code=401, content={"detail": "Token expired"})
            else:
                logger.warning(f"Invalid token | path: {request.url.path} | cause: {e.__cause__}")
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})