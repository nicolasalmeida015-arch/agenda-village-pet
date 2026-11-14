"""Lembretes da véspera (RF06).

No MVP o envio é registrado em log e devolve o link de WhatsApp pré-preenchido;
a troca por SMTP ou pela API oficial do WhatsApp fica isolada nesta função.
"""
import logging
from datetime import date, datetime, timedelta
from urllib.parse import quote

from sqlalchemy.orm import Session

from app import repositories as repo

log = logging.getLogger("lembretes")


def link_whatsapp(telefone: str, mensagem: str) -> str:
    numero = "55" + "".join(ch for ch in telefone if ch.isdigit())
    return f"https://wa.me/{numero}?text={quote(mensagem)}"


def enviar_lembretes_vespera(db: Session, hoje: date, agora: datetime) -> list[dict]:
    amanha = hoje + timedelta(days=1)
    enviados = []
    for ag in repo.agendamentos_do_dia(db, amanha):
        if ag.status not in ("agendado", "confirmado") or ag.lembrete_enviado_em is not None:
            continue
        tutor = ag.pet.tutor
        texto = (f"Olá, {tutor.nome}! Lembrete: {ag.servico.nome} do {ag.pet.nome} amanhã às "
                 f"{ag.data_hora_inicio:%H:%M} na Village Pet BR-116. Responda para confirmar ou cancelar.")
        ag.lembrete_enviado_em = agora
        log.info("Lembrete agendamento %s para %s", ag.id_agendamento, tutor.email)
        enviados.append({"id_agendamento": ag.id_agendamento,
                         "link_whatsapp": link_whatsapp(tutor.telefone_whatsapp, texto)})
    db.commit()
    return enviados
