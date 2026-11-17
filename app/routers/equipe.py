"""Rotas da equipe: agenda do dia, status, balcão (RF04, RF05), painel (RF08) e lembretes (RF06)."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import repositories as repo
from app.database import get_db
from app.models import Agendamento, Pet, Profissional, Usuario
from app.schemas import AgendamentoBalcao, AgendamentoPublico, AtualizarStatus, Indicadores, ItemAgendaDia
from app.security import exige_perfil
from app.services import agendamento_service as svc
from app.services import indicador_service, lembrete_service

router = APIRouter(prefix="/api/equipe", tags=["equipe"])
equipe = exige_perfil("atendente", "gerente")
gerente = exige_perfil("gerente")


@router.get("/agenda", response_model=list[ItemAgendaDia])
def agenda_do_dia(dia: date, usuario: Usuario = Depends(equipe), db: Session = Depends(get_db)):
    return [ItemAgendaDia(**AgendamentoPublico.model_validate(a).model_dump(),
                          pet_nome=a.pet.nome, pet_porte=a.pet.porte, pet_alergias=a.pet.alergias_observacoes,
                          servico_nome=a.servico.nome, profissional_nome=a.profissional.nome)
            for a in repo.agendamentos_do_dia(db, dia)]


@router.patch("/agendamentos/{id_agendamento}/status", response_model=AgendamentoPublico)
def mudar_status(id_agendamento: int, dados: AtualizarStatus, usuario: Usuario = Depends(equipe),
                 db: Session = Depends(get_db)):
    ag = db.get(Agendamento, id_agendamento)
    if ag is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    try:
        return svc.atualizar_status(db, ag, dados.status, datetime.now())
    except svc.RegraNegocioErro as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post("/agendamentos", response_model=AgendamentoPublico, status_code=201)
def agendar_balcao(dados: AgendamentoBalcao, usuario: Usuario = Depends(equipe), db: Session = Depends(get_db)):
    pet = db.get(Pet, dados.id_pet)
    if pet is None or not pet.ativo:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")
    try:
        return svc.criar_agendamento(db, pet, dados.id_servico, dados.id_profissional, dados.data_hora_inicio,
                                     dados.origem, usuario.id_usuario, datetime.now())
    except svc.ConflitoHorario as e:
        raise HTTPException(status_code=409, detail={"mensagem": str(e), "alternativas": [
            {"inicio": s.inicio.isoformat(), "id_profissional": s.id_profissional} for s in e.alternativas]}) from e


@router.get("/indicadores", response_model=Indicadores)
def indicadores(inicio: date, fim: date, usuario: Usuario = Depends(gerente), db: Session = Depends(get_db)):
    if fim < inicio:
        raise HTTPException(status_code=422, detail="A data final deve ser posterior à inicial.")
    ags = repo.agendamentos_periodo(db, inicio, fim)
    profs = list(db.scalars(select(Profissional)))
    dados = indicador_service.calcular_indicadores(ags, profs, inicio, fim)
    futuros = {a.id_pet for a in db.scalars(select(Agendamento).where(
        Agendamento.data_hora_inicio > datetime.now(), Agendamento.status.in_(("agendado", "confirmado"))))}
    pets = list(db.scalars(select(Pet).where(Pet.ativo.is_(True))))
    sem_retorno = indicador_service.pets_para_retorno(pets, repo.ultimos_concluidos_por_pet(db), futuros,
                                                      date.today())
    return Indicadores(inicio=inicio, fim=fim, pets_sem_retorno=len(sem_retorno), **dados)


@router.post("/lembretes/vespera")
def disparar_lembretes(usuario: Usuario = Depends(gerente), db: Session = Depends(get_db)):
    return lembrete_service.enviar_lembretes_vespera(db, date.today(), datetime.now())
