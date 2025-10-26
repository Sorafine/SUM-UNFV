from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor
import psycopg2
from database.db import get_db

aulas_bp = Blueprint('aulas', __name__)

# ======================================================
# 🏫 GESTIÓN DE AULAS
# ======================================================

@aulas_bp.route('/aulas', methods=['GET'])
def listar_aulas():
    """Muestra el listado de todas las aulas con sus detalles de ubicación y tipo."""
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                a.aula_id, 
                a.nombre_aula AS codigo,
                a.nombre_aula AS nombre,
                a.capacidad, 
                a.estado,
                tac.nombre_tipo AS tipo,
                pab.nombre_pabellon AS ubicacion 
            FROM aula a
            LEFT JOIN tipo_aula_cat tac ON a.tipo_aula_id = tac.tipo_aula_id
            LEFT JOIN pabellon pab ON a.pabellon_id = pab.pabellon_id
            ORDER BY a.nombre_aula ASC;
        """)
        aulas = cur.fetchall()
        return jsonify(aulas), 200

    except Exception as e:
        print(f"❌ Error al listar aulas: {e}")
        return jsonify({"error": "Error interno al listar las aulas."}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@aulas_bp.route('/aulas', methods=['POST'])
def crear_aula():
    data = request.json
    nombre_aula = data.get('nombre_aula')
    capacidad = data.get('capacidad')
    estado = data.get('estado')
    tipo_aula_id = data.get('tipo_aula_id')
    pabellon_id = data.get('pabellon_id')
    
    if not all([nombre_aula, capacidad, tipo_aula_id, pabellon_id, estado]):
        return jsonify({"error": "Faltan campos obligatorios."}), 400

    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO aula (nombre_aula, capacidad, estado, tipo_aula_id, pabellon_id)
            VALUES (%s, %s, %s, %s, %s);
        """, (nombre_aula, capacidad, estado, tipo_aula_id, pabellon_id))
        
        conn.commit()
        return jsonify({"mensaje": "Aula registrada exitosamente."}), 201
        
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        return jsonify({"error": "El nombre del aula ya existe o un ID es inválido."}), 400
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al crear aula: {e}")
        return jsonify({"error": "Error interno al registrar el aula."}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@aulas_bp.route('/aulas/<int:aula_id>', methods=['PUT'])
def actualizar_aula(aula_id):
    data = request.json
    nombre_aula = data.get('nombre_aula')
    capacidad = data.get('capacidad')
    estado = data.get('estado')
    tipo_aula_id = data.get('tipo_aula_id')
    pabellon_id = data.get('pabellon_id')

    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE aula
            SET nombre_aula=%s, capacidad=%s, estado=%s, tipo_aula_id=%s, pabellon_id=%s
            WHERE aula_id = %s;
        """, (nombre_aula, capacidad, estado, tipo_aula_id, pabellon_id, aula_id))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Aula no encontrada."}), 404
        
        conn.commit()
        return jsonify({"mensaje": "Aula actualizada exitosamente."}), 200
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al actualizar aula: {e}")
        return jsonify({"error": "Error interno al actualizar el aula."}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@aulas_bp.route('/aulas/<int:aula_id>', methods=['DELETE'])
def eliminar_aula(aula_id):
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        # Verificar si el aula está asignada en algún horario
        cur.execute("""
            SELECT COUNT(*) 
            FROM horario h
            JOIN seccion s ON h.seccion_id = s.seccion_id
            WHERE h.aula_id = %s AND s.estado = 'Vigente';
        """, (aula_id,))
        
        if cur.fetchone()[0] > 0:
            return jsonify({"error": "No se puede eliminar. El aula está asignada a uno o más horarios vigentes."}), 409

        # Proceder con la eliminación
        cur.execute("DELETE FROM aula WHERE aula_id = %s;", (aula_id,))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Aula no encontrada."}), 404
            
        conn.commit()
        return jsonify({"mensaje": "Aula eliminada correctamente."}), 200

    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al eliminar aula: {e}")
        return jsonify({"error": "Error interno al eliminar el aula."}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()