# src/main.py
import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory, session # Added session for redirect logic
from src.models.models import db, Andar, Lavanderia, HorarioDisponivel, Morador, Agendamento
from src.routes.api import api_bp, admin_bp # Import both blueprints
import datetime

app = Flask(__name__, static_folder="static")

# --- Database Configuration ---
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.urandom(24) # For session management

db.init_app(app)

# Register the blueprints
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp) # Register admin blueprint for HTML page serving

# --- Helper function to populate initial data (ensure test admin user) ---
def populate_initial_data():
    with app.app_context():
        if not Andar.query.first():
            print("Populating initial Andares...")
            for i in range(1, 16):
                db.session.add(Andar(numero_andar=i))
            db.session.commit()
            print("Andares populated.")

        if not HorarioDisponivel.query.first():
            print("Populating initial Horarios_Disponiveis...")
            horarios_data = [
                {"descricao_horario": "07:00-11:00", "hora_inicio": datetime.time(7, 0, 0), "hora_fim": datetime.time(11, 0, 0)},
                {"descricao_horario": "11:00-15:00", "hora_inicio": datetime.time(11, 0, 0), "hora_fim": datetime.time(15, 0, 0)},
                {"descricao_horario": "15:00-19:00", "hora_inicio": datetime.time(15, 0, 0), "hora_fim": datetime.time(19, 0, 0)},
                {"descricao_horario": "19:00-23:00", "hora_inicio": datetime.time(19, 0, 0), "hora_fim": datetime.time(23, 0, 0)},
            ]
            for h_data in horarios_data:
                db.session.add(HorarioDisponivel(**h_data))
            db.session.commit()
            print("Horarios_Disponiveis populated.")

        if not Lavanderia.query.first():
            print("Populating initial Lavanderias...")
            andares = Andar.query.all()
            for andar_obj in andares:
                db.session.add_all([
                    Lavanderia(id_andar_fk=andar_obj.id_andar, identificador_no_andar="Lavanderia 1"),
                    Lavanderia(id_andar_fk=andar_obj.id_andar, identificador_no_andar="Lavanderia 2")
                ])
            db.session.commit()
            print("Lavanderias populated.")

        # Ensure test user is admin
        test_morador = Morador.query.filter_by(email="morador_teste@email.com").first()
        if not test_morador:
            print("Populating test Morador (Admin)...")
            andar_teste = Andar.query.filter_by(numero_andar=1).first()
            if andar_teste:
                from werkzeug.security import generate_password_hash
                admin_user = Morador(
                    nome_completo="Morador Admin Teste",
                    email="morador_teste@email.com",
                    senha_hash=generate_password_hash("senha123"),
                    id_andar_fk=andar_teste.id_andar,
                    numero_apartamento="101",
                    is_admin=True # Set as admin
                )
                db.session.add(admin_user)
                db.session.commit()
                print("Test Morador (Admin) populated.")
            else:
                print("Could not populate test Morador: Andar 1 not found.")
        elif not test_morador.is_admin: # If user exists but is not admin
            print("Updating morador_teste@email.com to be an admin...")
            test_morador.is_admin = True
            db.session.commit()
            print("Morador_teste@email.com is now an admin.")


# --- Routes ---
@app.route("/")
def index():
    # If admin is logged in and tries to access root, maybe redirect to admin dashboard?
    # For now, just serve index.html for non-admin or non-logged-in users.
    if session.get("is_admin") and request.path == "/": # Basic check, could be more robust
         #This logic is tricky here, better handled by frontend or specific /login /admin_login routes
         pass # Let it serve index.html, admin can navigate to /admin/dashboard manually or via a link
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    if path == "admin_dashboard.html" and not session.get("is_admin"):
        # Protect direct access to admin_dashboard.html if not admin
        # The @admin_required decorator on the blueprint route /admin/dashboard is the primary protection
        return "Acesso não autorizado", 403 
    return send_from_directory(app.static_folder, path)

# --- Main execution ---
if __name__ == "__main__":
    with app.app_context():
        print("Dropping all tables for schema update (is_admin field)...")
        db.drop_all() # Drop all tables to ensure schema update with is_admin
        print("Creating database tables...")
        db.create_all()
        print("Database tables created.")
        populate_initial_data()
        print("Initial data population process completed.")
    
    app.run(host="0.0.0.0", port=5000, debug=True)

