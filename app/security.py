"""Autenticação e autorização (RNF01).

- Senhas: Argon2id com salt aleatório (argon2-cffi). Nunca texto puro, MD5 ou SHA-1.
- Sessão: JWT assinado com expiração curta e perfil do usuário.
- Força bruta: bloqueio temporário após 5 falhas em 15 minutos.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Usuario

_hasher = PasswordHasher()  # padrão da biblioteca: Argon2id
_bearer = HTTPBearer(auto_error=False)
_falhas: dict[str, list[datetime]] = defaultdict(list)
_revogados: set[str] = set()


def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except VerificationError:
        return False


def login_bloqueado(chave: str, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    janela = agora - timedelta(minutes=settings.janela_bloqueio_minutos)
    _falhas[chave] = [t for t in _falhas[chave] if t > janela]
    return len(_falhas[chave]) >= settings.max_tentativas_login


def registrar_falha(chave: str) -> None:
    _falhas[chave].append(datetime.now(timezone.utc))


def limpar_falhas(chave: str) -> None:
    _falhas.pop(chave, None)


def criar_token(usuario: Usuario) -> str:
    minutos = settings.token_minutes_tutor if usuario.perfil == "tutor" else settings.token_minutes_equipe
    agora = datetime.now(timezone.utc)
    payload = {"sub": str(usuario.id_usuario), "perfil": usuario.perfil,
               "iat": agora, "exp": agora + timedelta(minutes=minutos),
               "jti": f"{usuario.id_usuario}-{agora.timestamp()}"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def revogar_token(token: str) -> None:
    _revogados.add(token)


def usuario_atual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
                  db: Session = Depends(get_db)) -> Usuario:
    erro = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Faça login para continuar.")
    if cred is None or cred.credentials in _revogados:
        raise erro
    try:
        payload = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise erro from None
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.ativo:
        raise erro
    return usuario


def exige_perfil(*perfis: str):
    def verificador(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não permitido para o seu perfil.")
        return usuario
    return verificador
