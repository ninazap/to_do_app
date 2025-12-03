from fastapi import status, HTTPException



UserAlreadyExistsException = HTTPException(
    status_code = status.HTTP_409_CONFLICT,
    detail = "The user already exists"
)

UserNotFoundException = HTTPException(
    status_code = status.HTTP_404_NOT_FOUND,
    detail = "The user was not found"
)

UserIdNotFoundException = HTTPException(
    status_code = status.HTTP_404_NOT_FOUND,
    detail = "The user ID is missing"
)

IncorrectEmailOrPasswordException = HTTPException(
    status_code = status.HTTP_400_BAD_REQUEST,
    detail = "Incorrect email or password"
)

TokenExpiredException = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "The token has expired"
)

InvalidTokenFormatException = HTTPException(
    status_code = status.HTTP_400_BAD_REQUEST,
    detail = "The token is not valid"
)

TokenNoFound = HTTPException(
    status_code = status.HTTP_400_BAD_REQUEST,
    detail = "The token is missing in the header"
)

NoJwtException = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "The token is not valid"
)

NoUserIdException = HTTPException(
    status_code = status.HTTP_404_NOT_FOUND,
    detail = "User ID not found"
)

ForbiddenException = HTTPException(
    status_code = status.HTTP_403_FORBIDDEN,
    detail = "Not enough rights"
)

TokenInvalidFormatException = HTTPException(
    status_code = status.HTTP_400_BAD_REQUEST,
    detail = "Invalid token format. A 'Bearer <token>' is expected"
)