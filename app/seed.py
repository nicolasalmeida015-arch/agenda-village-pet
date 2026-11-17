"""Popula o banco com dados FICTÍCIOS para desenvolvimento e para o protótipo navegável.

Uso: python -m app.seed
"""
from datetime import date, datetime, time, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Agendamento, Pet, Profissional, Servico, Usuario
from app.security import gerar_hash


def popular() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Servico).count():
        print("Banco já populado.")
        return
    banho = Servico(nome="Banho", duracao_pequeno_min=60, duracao_medio_min=90, duracao_grande_min=120)
    higienica = Servico(nome="Banho e tosa higiênica", duracao_pequeno_min=90, duracao_medio_min=120,
                        duracao_grande_min=150)
    completa = Servico(nome="Tosa completa", duracao_pequeno_min=120, duracao_medio_min=150,
                       duracao_grande_min=180)
    db.add_all([banho, higienica, completa])
    db.add_all([
        Profissional(nome="Profissional A", hora_inicio=time(9), hora_fim=time(17), dias_trabalho="1,2,3,4,5",
                     servicos=[banho, higienica, completa]),
        Profissional(nome="Profissional B", hora_inicio=time(9), hora_fim=time(17), dias_trabalho="1,2,3,4,5",
                     servicos=[banho, higienica]),
    ])
    senha = gerar_hash("senha-de-teste-123")
    carla = Usuario(nome="Carla (fictícia)", email="carla@exemplo.com", telefone_whatsapp="11 90000-0000",
                    senha_hash=senha, perfil="tutor", consentimento_lgpd=True)
    db.add_all([carla,
                Usuario(nome="Atendente (fictícia)", email="atendente@exemplo.com",
                        telefone_whatsapp="11 90000-0001", senha_hash=senha, perfil="atendente",
                        consentimento_lgpd=True),
                Usuario(nome="Gerente (fictício)", email="gerente@exemplo.com",
                        telefone_whatsapp="11 90000-0002", senha_hash=senha, perfil="gerente",
                        consentimento_lgpd=True)])
    db.flush()
    thor = Pet(id_tutor=carla.id_usuario, nome="Thor", especie="cao", raca="Shih-tzu", porte="pequeno",
               pelagem="longa", alergias_observacoes="Pele sensível: usar shampoo hipoalergênico.")
    luna = Pet(id_tutor=carla.id_usuario, nome="Luna", especie="gato", raca="SRD", porte="pequeno", pelagem="media")
    bob = Pet(id_tutor=carla.id_usuario, nome="Bob", especie="cao", raca="Golden", porte="grande", pelagem="longa",
              intervalo_retorno_dias=7)
    db.add_all([thor, luna, bob])
    db.flush()
    _historico_demo(db, carla, [thor, luna, bob], [banho, higienica, completa])
    db.commit()
    print("Dados fictícios criados. Logins: carla@ / atendente@ / gerente@exemplo.com - senha-de-teste-123")


def _dias_uteis(inicio: date, quantidade: int, passo: int) -> list[date]:
    """Dias de terça a sábado (expediente dos profissionais fictícios), andando para trás (-1) ou frente (+1)."""
    dias, dia = [], inicio
    while len(dias) < quantidade:
        dia += timedelta(days=passo)
        if dia.weekday() in (1, 2, 3, 4, 5):
            dias.append(dia)
    return dias


def _historico_demo(db, tutor: Usuario, pets: list[Pet], servicos: list[Servico]) -> None:
    """Atendimentos FICTÍCIOS para o painel da gerência e os lembretes não ficarem vazios na demonstração."""
    prof_a, prof_b = db.query(Profissional).order_by(Profissional.id_profissional).all()
    hoje = date.today()
    status_passados = ["concluido", "concluido", "faltou", "concluido", "concluido", "cancelado",
                       "concluido", "faltou", "concluido", "concluido"]
    for i, (dia, status) in enumerate(zip(_dias_uteis(hoje, 10, -1), status_passados, strict=True)):
        pet, servico = pets[i % len(pets)], servicos[i % 2]
        inicio = datetime.combine(dia, time(9 + (i % 3) * 2))
        db.add(Agendamento(id_pet=pet.id_pet, id_servico=servico.id_servico,
                           id_profissional=(prof_a if i % 2 else prof_b).id_profissional, data_hora_inicio=inicio,
                           data_hora_fim=inicio + timedelta(minutes=servico.duracao_para(pet.porte)),
                           status=status, origem="online" if i % 3 else "balcao", criado_por=tutor.id_usuario))
    amanha = hoje + timedelta(days=1)
    if amanha.weekday() in (1, 2, 3, 4, 5):  # lembretes da véspera
        for hora, pet in ((10, pets[0]), (14, pets[1])):
            inicio = datetime.combine(amanha, time(hora))
            db.add(Agendamento(id_pet=pet.id_pet, id_servico=servicos[0].id_servico,
                               id_profissional=prof_a.id_profissional, data_hora_inicio=inicio,
                               data_hora_fim=inicio + timedelta(minutes=servicos[0].duracao_para(pet.porte)),
                               status="agendado", origem="online", criado_por=tutor.id_usuario))


if __name__ == "__main__":
    popular()
