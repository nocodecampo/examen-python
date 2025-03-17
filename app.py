from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
from db import get_connection

app = Flask(__name__)
app.secret_key = "123456"


# ✅ Página de inicio
@app.route("/")
def home():
    return render_template("home/home.html")

# ✅ Registrar nuevo alumno
@app.route("/registrar-alumno", methods=["GET", "POST"])
def registrar_alumno():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellidos = request.form["apellidos"]
        email = request.form["email"]

        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                sql = "INSERT INTO alumnos (nombre, apellidos, email) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nombre, apellidos, email))
                conexion.commit()
                flash("Alumno registrado con éxito.", "success")
        except pymysql.MySQLError:
            flash("Error al registrar el alumno. Verifica que el email no esté duplicado.", "danger")
        finally:
            conexion.close()

        return redirect(url_for("registrar_alumno"))

    return render_template("registro/registrar-alumno.html")

# ✅ Asignar calificación
@app.route("/asignar-nota", methods=["GET", "POST"])
def asignar_nota():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT alumno_id, nombre, apellidos FROM alumnos ORDER BY apellidos, nombre")
            alumnos = cursor.fetchall()

            cursor.execute("SELECT * FROM asignaturas ORDER BY nombre")
            asignaturas = cursor.fetchall()
    finally:
        conexion.close()

    if request.method == "POST":
        alumno_id = request.form["alumno_id"]
        asignatura_id = request.form["asignatura_id"]
        nota = request.form["nota"]

        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                # Verificar si el alumno ya tiene una nota en esta asignatura
                sql_verificar = """
                    SELECT * FROM calificaciones WHERE alumno_id = %s AND asignatura_id = %s
                """
                cursor.execute(sql_verificar, (alumno_id, asignatura_id))
                existe = cursor.fetchone()

                if existe:
                    flash("⚠️ Este alumno ya tiene una calificación para esta asignatura.", "warning")
                else:
                    # 🔹 Insertar la nueva calificación solo si no existe
                    sql_insertar = "INSERT INTO calificaciones (alumno_id, asignatura_id, nota) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insertar, (alumno_id, asignatura_id, nota))
                    conexion.commit()
                    flash("✅ Calificación asignada correctamente.", "success")

        except pymysql.MySQLError:
            flash("❌ Error al asignar la calificación.", "danger")
        finally:
            conexion.close()

        return redirect(url_for("asignar_nota"))

    return render_template("notas/asignar-nota.html", alumnos=alumnos, asignaturas=asignaturas)


# ✅ Ver notas con filtros por alumno y asignatura
@app.route("/ver-notas", methods=["GET"])
def ver_notas():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            # Obtener lista de alumnos para el filtro
            cursor.execute("SELECT alumno_id, nombre, apellidos FROM alumnos ORDER BY apellidos, nombre")
            alumnos = cursor.fetchall()

            # Obtener lista de asignaturas para el filtro
            cursor.execute("SELECT asignatura_id, nombre FROM asignaturas ORDER BY nombre")
            asignaturas = cursor.fetchall()

            # Obtener parámetros de búsqueda
            alumno_id = request.args.get("alumno_id")
            asignatura_id = request.args.get("asignatura_id")

            # Construcción de la consulta con filtros dinámicos
            consulta = """
                SELECT a.nombre AS alumno, a.apellidos AS apellidos, 
                       asig.nombre AS asignatura, c.nota 
                FROM calificaciones c
                JOIN alumnos a ON c.alumno_id = a.alumno_id
                JOIN asignaturas asig ON c.asignatura_id = asig.asignatura_id
                WHERE 1=1
            """
            valores = []

            if alumno_id:
                consulta += " AND a.alumno_id = %s"
                valores.append(alumno_id)

            if asignatura_id:
                consulta += " AND asig.asignatura_id = %s"
                valores.append(asignatura_id)

            consulta += " ORDER BY a.apellidos, a.nombre, asig.nombre"
            cursor.execute(consulta, valores)
            notas = cursor.fetchall()

    finally:
        conexion.close()

    return render_template("notas/ver-notas.html", notas=notas, alumnos=alumnos, asignaturas=asignaturas)



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)

