"""Cadastro de tutor, login e logout (RF01, RNF01)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import repositories as repo
from app import security
from app.database import get_db
from app.models import Usuario, agora_utc
from app.schemas import Login, Token, UsuarioCriar, UsuarioPublico

router = APIRouter(prefix="/api/auth", tags=["autenticação"])


@router.post("/cadastro", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCriar, db: Session = Depends(get_db)):
    if repo.usuario_por_email(db, dados.email):
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")
    usuario = Usuario(nome=dados.nome, email=dados.email.lower(), telefone_whatsapp=dados.telefone_whatsapp,
                      senha_hash=security.gerar_hash(dados.senha), perfil="tutor",
                      consentimento_lgpd=True, data_consentimento=agora_utc())
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(dados: Login, request: Request, db: Session = Depends(get_db)):
    chave = f"{dados.email.lower()}|{request.client.host if request.client else '-'}"
    if security.login_bloqueado(chave):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde 15 minutos e tente de novo.")
    usuario = repo.usuario_por_email(db, dados.email)
    if usuario is None or not usuario.ativo or not security.verificar_senha(dados.senha, usuario.senha_hash):
        security.registrar_falha(chave)
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    security.limpar_falhas(chave)
    return Token(access_token=security.criar_token(usuario), perfil=usuario.perfil)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
           _: Usuario = Depends(security.usuario_atual)):
    security.revogar_token(cred.credentials)


@router.get("/eu", response_model=UsuarioPublico)
def eu(usuario: Usuario = Depends(security.usuario_atual)):
    return usuario
