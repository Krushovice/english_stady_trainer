import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext() -> None:
    assert hash_password("correcthorsebattery") != "correcthorsebattery"


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("correcthorsebattery")
    assert verify_password("correcthorsebattery", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("correcthorsebattery")
    assert verify_password("wrong-password", hashed) is False


def test_access_token_round_trip() -> None:
    token = create_access_token(subject="user-123")
    assert decode_access_token(token) == "user-123"


def test_decode_rejects_tampered_token() -> None:
    token = create_access_token(subject="user-123")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token + "tampered")
