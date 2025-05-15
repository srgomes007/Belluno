# src/routes/api.py
from flask import Blueprint, jsonify, request, session, current_app, send_from_directory
from src.models.models import db, Andar, Lavanderia, HorarioDisponivel, Morador, Agendamento
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from functools import wraps
import datetime

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")
admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin") # Separate blueprint for admin HTML page

# --- Decorator for Admin Routes ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "morador_id" not in session:
            return jsonify({"error": "Não autenticado"}), 401
        morador = Morador.query.get(session["morador_id"])
        if not morador or not morador.is_admin:
            return jsonify({"error": "Acesso não autorizado. Requer privilégios de administrador."}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Autenticação (Atualizada para incluir is_admin na sessão) ---
@api_bp.route("/register", methods=["POST"])
def register_morador():
    data = request.get_json()
    nome_completo = data.get("nome_completo")
    email = data.get("email")
    senha = data.get("senha")
    andar_num = data.get("andar")
    numero_apartamento = data.get("apartamento")
    is_admin_val = data.get("is_admin", False) # Default to False if not provided

    if not all([nome_completo, email, senha, andar_num, numero_apartamento]):
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    andar_obj = Andar.query.filter_by(numero_andar=andar_num).first()
    if not andar_obj:
        return jsonify({"error": f"Andar {andar_num} não encontrado."}), 404

    if Morador.query.filter_by(email=email).first():
        return jsonify({"error": "E-mail já cadastrado."}), 409

    senha_hash = generate_password_hash(senha)
    novo_morador = Morador(
        nome_completo=nome_completo,
        email=email,
        senha_hash=senha_hash,
        id_andar_fk=andar_obj.id_andar,
        numero_apartamento=numero_apartamento,
        is_admin=is_admin_val
    )
    db.session.add(novo_morador)
    try:
        db.session.commit()
        return jsonify({"message": "Morador cadastrado com sucesso!", "morador_id": novo_morador.id_morador}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Erro ao cadastrar morador. Verifique os dados."}), 500

@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"error": "E-mail e senha são obrigatórios"}), 400

    morador = Morador.query.filter_by(email=email).first()

    if morador and check_password_hash(morador.senha_hash, senha):
        session["morador_id"] = morador.id_morador
        session["andar_id"] = morador.id_andar_fk
        session["apartamento"] = morador.numero_apartamento
        session["is_admin"] = morador.is_admin # Adiciona is_admin à sessão
        return jsonify({
            "message": "Login bem-sucedido!",
            "morador": {
                "id": morador.id_morador,
                "nome": morador.nome_completo,
                "email": morador.email,
                "andar_num": morador.andar_residencia.numero_andar,
                "apartamento": morador.numero_apartamento,
                "is_admin": morador.is_admin
            }
        }), 200
    return jsonify({"error": "E-mail ou senha inválidos."}), 401

@api_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout bem-sucedido!"}), 200

@api_bp.route("/user_info", methods=["GET"])
def get_user_info():
    if "morador_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401
    
    morador = Morador.query.get(session["morador_id"])
    if not morador:
        session.clear()
        return jsonify({"error": "Usuário não encontrado"}), 404

    return jsonify({
        "id": morador.id_morador,
        "nome": morador.nome_completo,
        "email": morador.email,
        "andar_num": morador.andar_residencia.numero_andar,
        "apartamento": morador.numero_apartamento,
        "andar_id_fk": morador.id_andar_fk,
        "is_admin": morador.is_admin
    }), 200

# --- Rotas de Agendamento (Atualizada para considerar status da lavanderia) ---
@api_bp.route("/laundries/slots", methods=["GET"])
def get_laundry_slots():
    if "morador_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401

    date_str = request.args.get("date")
    andar_id_fk = session.get("andar_id")

    if not date_str or not andar_id_fk:
        return jsonify({"error": "Data e informação do andar são obrigatórios."}), 400

    try:
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    # Filtra lavanderias ativas do andar do morador
    lavanderias_andar = Lavanderia.query.filter_by(id_andar_fk=andar_id_fk, status="ativa").all()
    todos_horarios = HorarioDisponivel.query.all()

    response_slots = {}
    for lavanderia in lavanderias_andar:
        response_slots[lavanderia.id_lavanderia] = {
            "identificador": lavanderia.identificador_no_andar,
            "slots": []
        }
        agendamentos_existentes = Agendamento.query.filter_by(
            id_lavanderia_fk=lavanderia.id_lavanderia,
            data_agendamento=selected_date,
            status_agendamento="confirmado"
        ).all()
        horarios_ocupados_ids = {ag.id_horario_fk for ag in agendamentos_existentes}

        for horario in todos_horarios:
            response_slots[lavanderia.id_lavanderia]["slots"].append({
                "id_horario": horario.id_horario,
                "descricao": horario.descricao_horario,
                "ocupado": horario.id_horario in horarios_ocupados_ids
            })
    return jsonify(response_slots), 200

@api_bp.route("/bookings", methods=["POST"])
def create_booking():
    if "morador_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401

    data = request.get_json()
    id_lavanderia = data.get("id_lavanderia")
    id_horario = data.get("id_horario")
    date_str = data.get("data_agendamento")
    morador_id = session["morador_id"]

    if not all([id_lavanderia, id_horario, date_str]):
        return jsonify({"error": "id_lavanderia, id_horario e data_agendamento são obrigatórios."}), 400

    try:
        data_agendamento = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD."}), 400
    
    lavanderia_obj = Lavanderia.query.get(id_lavanderia)
    if not lavanderia_obj or lavanderia_obj.id_andar_fk != session.get("andar_id"):
        return jsonify({"error": "Lavanderia inválida ou não pertence ao seu andar."}), 403
    if lavanderia_obj.status != "ativa":
        return jsonify({"error": "Esta lavanderia não está ativa e não pode ser agendada."}), 403

    novo_agendamento = Agendamento(
        id_morador_fk=morador_id,
        id_lavanderia_fk=id_lavanderia,
        id_horario_fk=id_horario,
        data_agendamento=data_agendamento
    )
    try:
        db.session.add(novo_agendamento)
        db.session.commit()
        return jsonify({
            "message": "Agendamento criado com sucesso!", 
            "agendamento": {
                "id_agendamento": novo_agendamento.id_agendamento,
                "data": novo_agendamento.data_agendamento.isoformat(),
                "horario": novo_agendamento.horario_agendado.descricao_horario,
                "lavanderia": novo_agendamento.lavanderia_agendada.identificador_no_andar
            }
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Este horário já está reservado ou ocorreu um erro."}), 409

@api_bp.route("/bookings/mine", methods=["GET"])
def get_my_bookings():
    if "morador_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401

    morador_id = session["morador_id"]
    agendamentos = Agendamento.query.filter_by(id_morador_fk=morador_id, status_agendamento="confirmado")\
                                    .order_by(Agendamento.data_agendamento, Agendamento.id_horario_fk).all()
    
    response_data = []
    for ag in agendamentos:
        response_data.append({
            "id_agendamento": ag.id_agendamento,
            "data": ag.data_agendamento.isoformat(),
            "horario_desc": ag.horario_agendado.descricao_horario,
            "lavanderia_id": ag.id_lavanderia_fk,
            "lavanderia_desc": ag.lavanderia_agendada.identificador_no_andar,
            "andar_lavanderia": ag.lavanderia_agendada.andar.numero_andar
        })
    return jsonify(response_data), 200

@api_bp.route("/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    if "morador_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401

    agendamento = Agendamento.query.get(booking_id)

    if not agendamento:
        return jsonify({"error": "Agendamento não encontrado."}), 404

    if agendamento.id_morador_fk != session["morador_id"] and not session.get("is_admin"):
         return jsonify({"error": "Você não tem permissão para cancelar este agendamento."}), 403

    agendamento.status_agendamento = "cancelado"
    try:
        db.session.commit()
        return jsonify({"message": "Agendamento cancelado com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao cancelar agendamento: {str(e)}"}), 500

# --- Rotas Administrativas ---
@admin_bp.route("/dashboard") # Servir a página HTML do dashboard
@admin_required
def admin_dashboard_page():
    # current_app.static_folder é /home/ubuntu/app_lavanderia_condominio/src/static
    return send_from_directory(current_app.static_folder, "admin_dashboard.html")

@api_bp.route("/admin/all_bookings", methods=["GET"])
@admin_required
def get_all_bookings():
    # Adicionar filtros por data e andar, se fornecidos
    query = Agendamento.query.join(Morador).join(Lavanderia).join(Andar).join(HorarioDisponivel)
    
    date_start_str = request.args.get("date_start")
    date_end_str = request.args.get("date_end")
    andar_num_str = request.args.get("andar")

    if date_start_str:
        try:
            date_start = datetime.datetime.strptime(date_start_str, "%Y-%m-%d").date()
            query = query.filter(Agendamento.data_agendamento >= date_start)
        except ValueError:
            return jsonify({"error": "Formato de data de início inválido."}), 400
    if date_end_str:
        try:
            date_end = datetime.datetime.strptime(date_end_str, "%Y-%m-%d").date()
            query = query.filter(Agendamento.data_agendamento <= date_end)
        except ValueError:
            return jsonify({"error": "Formato de data de fim inválido."}), 400
    if andar_num_str:
        try:
            andar_num = int(andar_num_str)
            query = query.filter(Andar.numero_andar == andar_num)
        except ValueError:
            return jsonify({"error": "Número do andar inválido."}), 400

    agendamentos = query.order_by(Agendamento.data_agendamento.desc(), HorarioDisponivel.hora_inicio.desc()).all()
    response_data = []
    for ag in agendamentos:
        response_data.append({
            "id_agendamento": ag.id_agendamento,
            "data": ag.data_agendamento.isoformat(),
            "horario_desc": ag.horario_agendado.descricao_horario,
            "andar_num": ag.lavanderia_agendada.andar.numero_andar,
            "lavanderia_identificador": ag.lavanderia_agendada.identificador_no_andar,
            "morador_nome": ag.morador_responsavel.nome_completo,
            "morador_apto": ag.morador_responsavel.numero_apartamento,
            "status_agendamento": ag.status_agendamento
        })
    return jsonify(response_data), 200

@api_bp.route("/admin/all_laundries", methods=["GET"])
@admin_required
def get_all_laundries_status():
    lavanderias = Lavanderia.query.join(Andar).order_by(Andar.numero_andar, Lavanderia.identificador_no_andar).all()
    response_data = []
    for lav in lavanderias:
        response_data.append({
            "id_lavanderia": lav.id_lavanderia,
            "andar_num": lav.andar.numero_andar,
            "identificador": lav.identificador_no_andar,
            "status": lav.status
        })
    return jsonify(response_data), 200

@api_bp.route("/admin/laundry/<int:laundry_id>/status", methods=["PUT"])
@admin_required
def update_laundry_status(laundry_id):
    data = request.get_json()
    new_status = data.get("status")

    if not new_status or new_status not in ["ativa", "manutencao"]:
        return jsonify({"error": "Status inválido. Use 'ativa' ou 'manutencao'."}), 400

    lavanderia = Lavanderia.query.get(laundry_id)
    if not lavanderia:
        return jsonify({"error": "Lavanderia não encontrada."}), 404

    # Alerta sobre agendamentos existentes se for colocar em manutenção
    if new_status == "manutencao" and lavanderia.status == "ativa":
        agendamentos_futuros = Agendamento.query.filter(
            Agendamento.id_lavanderia_fk == laundry_id,
            Agendamento.data_agendamento >= datetime.date.today(),
            Agendamento.status_agendamento == "confirmado"
        ).count()
        if agendamentos_futuros > 0:
            # Apenas um aviso, a ação prossegue
            current_app.logger.warning(f"Lavanderia {laundry_id} colocada em manutenção possui {agendamentos_futuros} agendamentos futuros.")
    
    lavanderia.status = new_status
    try:
        db.session.commit()
        return jsonify({"message": "Status da lavanderia atualizado com sucesso!", "lavanderia": {
            "id_lavanderia": lavanderia.id_lavanderia,
            "status": lavanderia.status
        }}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar status da lavanderia: {e}")
        return jsonify({"error": f"Erro ao atualizar status: {str(e)}"}), 500

@api_bp.route("/admin/floors", methods=["GET"])
@admin_required # Ou pode ser aberto se for só para popular um select no frontend
def get_all_floors():
    andares = Andar.query.order_by(Andar.numero_andar).all()
    return jsonify([{"id_andar": andar.id_andar, "numero_andar": andar.numero_andar} for andar in andares]), 200

