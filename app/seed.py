"""Popula o banco com dados FICTÍCIOS para desenvolvimento e para o protótipo navegável.

Uso: python -m app.seed
"""
from datetime import time

from app.database import Base, SessionLocal, engine
from app.models import Pet, Profissional, Servico, Usuario
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
    db.add(Pet(id_tutor=carla.id_usuario, nome="Thor", especie="cao", raca="Shih-tzu", porte="pequeno",
               pelagem="longa", alergias_observacoes="Pele sensível: usar shampoo hipoalergênico."))
    db.commit()
    print("Dados fictícios criados. Logins: carla@ / atendente@ / gerente@exemplo.com - senha-de-teste-123")


if __name__ == "__main__":
    popular()
