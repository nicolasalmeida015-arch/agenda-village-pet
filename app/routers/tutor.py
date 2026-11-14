"""Rotas do tutor: pets, serviços, horários livres e agendamento online (RF01-RF03)."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import repositories as repo
from app.database import get_db
from app.models import Pet, Usuario
from app.schemas import AgendamentoCriar, AgendamentoPublico, Horario, PetCriar, PetPublico, ServicoPublico
from app.security import exige_perfil, usuario_atual
from app.services import agendamento_service as svc

router = APIRouter(prefix="/api", tags=["tutor"])
tutor = exige_perfil("tutor")


def agora() -> datetime:
    return datetime.now()


@router.get("/servicos", response_model=list[ServicoPublico])
def listar_servicos(db: Session = Depends(get_db)):
    return repo.servicos_ativos(db)


@router.get("/pets", response_model=list[PetPublico])
def meus_pets(usuario: Usuario = Depends(tutor), db: Session = Depends(get_db)):
    return repo.pets_do_tutor(db, usuario.id_usuario)


@router.post("/pets", response_model=PetPublico, status_code=status.HTTP_201_CREATED)
def cadastrar_pet(dados: PetCriar, usuario: Usuario = Depends(tutor), db: Session = Depends(get_db)):
    pet = Pet(id_tutor=usuario.id_usuario, **dados.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def _pet_ou_404(db: Session, id_pet: int, usuario: Usuario) -> Pet:
    pet = repo.pet_do_tutor(db, id_pet, usuario.id_usuario)
    if pet is None:  # 404 também para pet de outro tutor: não revela que o recurso existe (IDOR)
        raise HTTPException(status_code=404, detail="Pet não encontrado.")
    return pet


@router.get("/disponibilidade", response_model=list[Horario])
def disponibilidade(id_pet: int, id_servico: int, dia: date,
                    usuario: Usuario = Depends(tutor), db: Session = Depends(get_db)):
    pet = _pet_ou_404(db, id_pet, usuario)
    try:
        slots = svc.horarios_livres(db, id_servico, pet, dia, agora())
    except svc.RegraNegocioErro as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return [Horario(inicio=s.inicio, fim=s.fim, id_profissional=s.id_profissional, profissional=s.profissional)
            for s in slots]


@router.post("/agendamentos", response_model=AgendamentoPublico, status_code=status.HTTP_201_CREATED)
def agendar(dados: AgendamentoCriar, usuario: Usuario = Depends(tutor), db: Session = Depends(get_db)):
    pet = _pet_ou_404(db, dados.id_pet, usuario)
    try:
        return svc.criar_agendamento(db, pet, dados.id_servico, dados.id_profissional, dados.data_hora_inicio,
                                     "online", usuario.id_usuario, agora())
    except svc.ConflitoHorario as e:
        raise HTTPException(status_code=409, detail={
            "mensagem": str(e),
            "alternativas": [{"inicio": s.inicio.isoformat(), "id_profissional": s.id_profissional,
                              "profissional": s.profissional} for s in e.alternativas]}) from e
    except svc.RegraNegocioErro as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/agendamentos", response_model=list[AgendamentoPublico])
def meus_agendamentos(usuario: Usuario = Depends(tutor), db: Session = Depends(get_db)):
    return repo.agendamentos_do_tutor(db, usuario.id_usuario)


@router.post("/agendamentos/{id_agendamento}/cancelar", response_model=AgendamentoPublico)
def cancelar(id_agendamento: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    ag = next((a for a in repo.agendamentos_do_tutor(db, usuario.id_usuario)
               if a.id_agendamento == id_agendamento), None)
    if ag is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    try:
        return svc.atualizar_status(db, ag, "cancelado", agora())
    except svc.RegraNegocioErro as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
