# src/models/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class Andar(db.Model):
    __tablename__ = "Andares"
    id_andar = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_andar = db.Column(db.Integer, nullable=False, unique=True)

    lavanderias = db.relationship("Lavanderia", backref="andar")
    moradores = db.relationship("Morador", backref="andar_residencia")

    def __repr__(self):
        return f"<Andar {self.numero_andar}>"

class Lavanderia(db.Model):
    __tablename__ = "Lavanderias"
    id_lavanderia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_andar_fk = db.Column(db.Integer, db.ForeignKey("Andares.id_andar"), nullable=False)
    identificador_no_andar = db.Column(db.String(50), nullable=False) # Ex: "Lavanderia 1", "Lavanderia 2"
    status = db.Column(db.String(20), nullable=False, default="ativa") # ativa, manutencao

    agendamentos = db.relationship("Agendamento", backref="lavanderia_agendada")

    __table_args__ = (db.UniqueConstraint("id_andar_fk", "identificador_no_andar", name="uq_lavanderia_andar_identificador"),)

    def __repr__(self):
        return f"<Lavanderia {self.identificador_no_andar} - Andar {self.andar.numero_andar}>"

class HorarioDisponivel(db.Model):
    __tablename__ = "Horarios_Disponiveis"
    id_horario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    descricao_horario = db.Column(db.String(50), nullable=False, unique=True) # Ex: "07:00-11:00"
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)

    agendamentos = db.relationship("Agendamento", backref="horario_agendado")

    def __repr__(self):
        return f"<HorarioDisponivel {self.descricao_horario}>"

class Morador(db.Model):
    __tablename__ = "Moradores"
    id_morador = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_completo = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False) # Armazenar hash da senha
    id_andar_fk = db.Column(db.Integer, db.ForeignKey("Andares.id_andar"), nullable=False)
    numero_apartamento = db.Column(db.String(10), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    data_cadastro = db.Column(db.DateTime(timezone=True), server_default=func.now())
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False) # Novo campo para administrador

    agendamentos = db.relationship("Agendamento", backref="morador_responsavel")

    def __repr__(self):
        return f"<Morador {self.nome_completo} - Apt {self.numero_apartamento} / Andar {self.andar_residencia.numero_andar} {'(Admin)' if self.is_admin else ''}>"

class Agendamento(db.Model):
    __tablename__ = "Agendamentos"
    id_agendamento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_morador_fk = db.Column(db.Integer, db.ForeignKey("Moradores.id_morador"), nullable=False)
    id_lavanderia_fk = db.Column(db.Integer, db.ForeignKey("Lavanderias.id_lavanderia"), nullable=False)
    id_horario_fk = db.Column(db.Integer, db.ForeignKey("Horarios_Disponiveis.id_horario"), nullable=False)
    data_agendamento = db.Column(db.Date, nullable=False)
    data_criacao = db.Column(db.DateTime(timezone=True), server_default=func.now())
    status_agendamento = db.Column(db.String(20), nullable=False, default="confirmado") # confirmado, cancelado, concluido

    __table_args__ = (db.UniqueConstraint("id_lavanderia_fk", "id_horario_fk", "data_agendamento", name="uq_agendamento_lav_hor_data"),)

    def __repr__(self):
        return f"<Agendamento {self.id_agendamento} - Morador {self.id_morador_fk} em {self.data_agendamento} {self.horario_agendado.descricao_horario}>"

