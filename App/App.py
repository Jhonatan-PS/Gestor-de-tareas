from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature

app = Flask(__name__)

# Configurar la conexión a base de datos
app.secret_key = "15102005"  # Asegúrate de que sea lo suficientemente complejo y secreto
serializer = URLSafeTimedSerializer(app.secret_key)

def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="gestor de tareas"
    )
    return db

# Configuración del servidor de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'JhonatanPulido1500@gmail.com'  # Cambiado a MAIL_USERNAME
app.config['MAIL_PASSWORD'] = 'okfg pbio ovvx csak'  # Considera usar variables de entorno para la seguridad
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = ('Gestor de tareas', 'JhonatanPulido1500@gmail.com')
mail = Mail(app)

def Enviar_correo(email):
    if email:
        # Se genera un token para el correo electrónico proporcionado
        token = serializer.dumps(email, salt='Restablecimiento de contraseña')
        # Se crea la URL
        enlace = url_for('Restablecercontraseña', token=token, _external=True)
        # Se crea el mensaje del correo enviado
        mensaje = Message(subject='Recuperar contraseña', recipients=[email], body=f'Para restablecer la contraseña, haz clic en el siguiente enlace: {enlace}')
        mail.send(mensaje)
    else:
        raise ValueError("El correo electrónico proporcionado es inválido")

@app.route('/Restablecer_contraseña/<token>', methods=['GET', 'POST'])
def Restablecercontraseña(token):
    if request.method == 'POST':
        nueva_contrasena = request.form.get('nueva_contraseña')
        confirmar_contrasena = request.form.get('confirmar_contraseña')
        
        # Verificar que las contraseñas sean iguales
        if nueva_contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('Restablecercontraseña', token=token))
        
        # Actualizar contraseñas en la base de datos
        db = get_db_connection()
        cursor = db.cursor()
        email = serializer.loads(token, salt='Restablecimiento de contraseña', max_age=50000)
        consulta = "UPDATE usuarios SET Contraseña = %s WHERE Email = %s"
        cursor.execute(consulta, (nueva_contrasena, email))
        db.commit()
        db.close()
        flash("Tu contraseña ha sido actualizada exitosamente")
        return redirect(url_for('IngresoUsuario'))
    
    return render_template('Restablecer_contraseña.html')

@app.route('/Recuperar_contraseña', methods=['GET', 'POST'])
def Recuperarcontraseña():
    if request.method == 'POST':
        email = request.form.get('email_usuario')
        if email:
            Enviar_correo(email)
            flash("Se ha enviado un correo para restablecer tu contraseña")
            return redirect(url_for('IngresoUsuario'))
        else:
            flash("Por favor, introduce un correo electrónico válido")
        
    return render_template('Recuperar_contraseña.html')

# Crear las rutas
@app.route('/')
def Inicio():
    return render_template('Inicio.html')

@app.route('/Registro',methods=['GET' , 'POST'])  
def RegistrarUsuario():    
    if request.method == 'POST':
        db = get_db_connection()
        cursor = db.cursor()

        nombres_usuario = request.form.get('nombres_usuario')
        apellidos_usuario = request.form.get('apellidos_usuario')
        email_usuario = request.form.get('email_usuario')         
        nombre_usuario = request.form.get('nombre_usuario') 
        contraseña = request.form.get('contraseña')
        rol = request.form.get('rol') 
        
        # Verificar usuario y email si ya existe      
        cursor.execute("SELECT * FROM usuarios WHERE Nombre_usuario = %s OR Email = %s",(nombre_usuario,email_usuario))
        resultado = cursor.fetchone()
        
        if resultado:
            print ("Usuario o email ya registrado")
            render_template('Registro_usuario.html')
        else:        
            # Insertar usuarios a la tabla usuarios        
            cursor.execute("INSERT INTO usuarios(Nombres,Apellidos,Email,Nombre_usuario,Contraseña,Rol) VALUES(%s,%s,%s,%s,%s,%s)",(nombres_usuario,apellidos_usuario,email_usuario,nombre_usuario,contraseña,rol))
            db.commit()
            print("¡Usuario registrado!")                 
            return redirect(url_for('RegistrarUsuario'))        
    return render_template('Registro_usuario.html')

@app.route('/Ingreso', methods=['GET', 'POST'])
def IngresoUsuario():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        # Obtener las credenciales de usuario
        nombre_usuario = request.form.get('nombre_usuario')
        contraseña = request.form.get('contraseña')

        cursor.execute("SELECT ID_Usuario, Contraseña, Rol FROM usuarios WHERE Nombre_usuario = %s", (nombre_usuario,))
        resultado = cursor.fetchone()
        if resultado:
            id_usuario, stored_password, rol = resultado
            if contraseña == stored_password:
                session['id_usuario'] = id_usuario
                session['nombre_usuario'] = nombre_usuario
                print(f"ID de usuario almacenado en la sesión: {id_usuario}")
                print(f"Nombre de usuario almacenado en la sesión: {nombre_usuario}")
                flash('Credenciales validas','success')
                if rol == 'Administrador':
                    return redirect(url_for('Interfaz_administrador', _external=True) + f'?nombre_usuario={session["nombre_usuario"]}')
                elif rol == 'Usuario':
                    return redirect(url_for('Interfaz_usuario', _external=True) + f'?nombre_usuario={session["nombre_usuario"]}')
            else:
                print("Contraseña incorrecta")
                flash('Usuario o contraseña invalidos','error')
        else:
            print("Usuario no encontrado")
            flash('Usuario no encontrado', 'error')
    return render_template('Inicio_sesion.html') 

@app.route('/Administrador')
def Interfaz_administrador():      
    nombre_usuario = session.get('nombre_usuario') 
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    print(f"Nombre de usuario recuperado de la sesión: {nombre_usuario}") 
           
    return render_template('Interfaz_administrador.html', nombre_usuario=nombre_usuario)

@app.route('/Listar_usuarios')
def Mostrar_usuarios():
    nombre_usuario = session.get('nombre_usuario')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Consulta para obtener todos los usuarios
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()

    # Pasar la lista de usuarios a la plantilla
    return render_template('Interfaz_administrador.html', usuarios=usuarios, nombre_usuario=nombre_usuario) 

@app.route('/borrar_usuario/<int:id>', methods=['GET'])
def borrar_usuario(id):                 
    # Verifica si el usuario está autenticado y autorizado para borrar
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Elimina todas las tareas relacionadas con el usuario
        cursor.execute("DELETE FROM tareas WHERE ID_Usuario = %s", (id,))
        db.commit()
        
        # Luego, elimina el usuario
        cursor.execute("DELETE FROM usuarios WHERE ID_Usuario = %s", (id,))
        db.commit()
        
        # Mensaje de depuración
        print(f"Usuario con ID {id} ha sido eliminado.")
        
    except mysql.connector.errors.IntegrityError:
        # Maneja el error de integridad referencial
        flash('No se puede eliminar este usuario porque tiene tareas asociadas.', 'error')
        return redirect(url_for('Mostrar_usuarios'))
    
    # Redirige a la página de lista de usuarios
    return redirect(url_for('Mostrar_usuarios'))

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    
    # Configura el cursor para usar un cursor de diccionario
    cursor = db.cursor(dictionary=True)

    # Procesa la solicitud POST o muestra el formulario para el método GET
    if request.method == 'POST':
        # Procesar los datos editados desde el formulario
        nombres = request.form.get('nombres_usuario')
        apellidos = request.form.get('apellidos_usuario')
        email = request.form.get('email_usuario')
        nombre_usuario_editado = request.form.get('nombre_usuario')
        rol = request.form.get('rol')

        # Actualizar el usuario en la base de datos
        cursor.execute(
            "UPDATE usuarios SET Nombres = %s, Apellidos = %s, Email = %s, Nombre_usuario = %s, Rol = %s WHERE ID_Usuario = %s",
            (nombres, apellidos, email, nombre_usuario_editado, rol, id)
        )
        db.commit()
        print(f"Usuario con ID {id} ha sido editado.")
        return redirect(url_for('Mostrar_usuarios'))

    # Si el método es GET, muestra el formulario con los datos actuales del usuario
    cursor.execute("SELECT * FROM usuarios WHERE ID_Usuario = %s", (id,))
    usuario = cursor.fetchone()

    # Mensaje de depuración para verificar los datos del usuario
    print(f"Datos del usuario: {usuario}")

    # Verifica si el usuario existe
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('Mostrar_usuarios'))

    # Renderiza el formulario de edición con los datos del usuario
    return render_template('Modificar_usuario.html', usuario=usuario)

@app.route('/Listar_tareas')
def Mostrar_tareas():
    nombre_usuario = session.get('nombre_usuario')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Consulta para obtener todas las tareas
    cursor.execute("SELECT * FROM tareas")
    tareas = cursor.fetchall()

    # Pasar la lista de usuarios a la plantilla
    return render_template('Interfaz_administrador.html', tareas=tareas, nombre_usuario=nombre_usuario) 

@app.route('/borrar_tarea/<int:id>', methods=['GET'])
def borrar_tarea(id):
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    cursor = db.cursor()

    # Ejecuta la consulta para borrar la tarea con el ID especificado
    cursor.execute("DELETE FROM tareas WHERE ID_Tarea = %s", (id,))
    db.commit()  # Confirma la transacción
    
    # Mensaje de depuración
    print(f"Tarea con ID {id} ha sido eliminada.")

    # Redirige a la página de lista de tareas
    return redirect(url_for('Mostrar_tareas'))

@app.route('/editar_tarea/<int:id>', methods=['GET', 'POST'])
def editar_tarea(id):
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()

    # Configura el cursor para usar un cursor de diccionario
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Procesar los datos editados desde el formulario
        nombre_tarea = request.form.get('nombre_tarea')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        estado = request.form.get('estado')

        # Actualizar la tarea en la base de datos
        cursor.execute(
            "UPDATE tareas SET Nombre = %s, Fecha_Inicio = %s, Fecha_Fin = %s, Estado = %s WHERE ID_Tarea = %s",
            (nombre_tarea, fecha_inicio, fecha_fin, estado, id)
        )
        db.commit()
        print(f"Tarea con ID {id} ha sido editada.")
        return redirect(url_for('Mostrar_tareas'))

    # Si el método es GET, muestra el formulario con los datos actuales de la tarea
    cursor.execute("SELECT * FROM tareas WHERE ID_Tarea = %s", (id,))
    tarea = cursor.fetchone()

    # Mensaje de depuración para verificar los datos de la tarea
    print(f"Datos de la tarea: {tarea}")

    # Verifica si la tarea existe
    if not tarea:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('Mostrar_tareas'))

    # Renderiza la plantilla de edición con los datos de la tarea
    return render_template('Modificar_tarea.html', tarea=tarea)

@app.route('/Registro-usuarios-interfaz-administrador',methods=['GET' , 'POST'])  
def RegistrarUsuario_interfaz_administrador():
    # Obtén el nombre de usuario de la sesión
    nombre_usuario = session.get('nombre_usuario')
    
    # Verifica si el usuario está autenticado
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    print(f"Nombre de usuario recuperado de la sesión: {nombre_usuario}") 
    
    db = get_db_connection()
    cursor = db.cursor()
    
    if request.method == 'POST':
        nombres_usuario = request.form.get('nombres_usuario')
        apellidos_usuario = request.form.get('apellidos_usuario')
        email_usuario = request.form.get('email_usuario')         
        nombre_usuario = request.form.get('nombre_usuario') 
        contraseña = request.form.get('contraseña')
        rol = request.form.get('rol') 
        
        # Verificar usuario y email si ya existe      
        cursor.execute("SELECT * FROM usuarios WHERE Nombre_usuario = %s OR Email = %s",(nombre_usuario,email_usuario))
        resultado = cursor.fetchone()
        
        if resultado:
            print ("Usuario o email ya registrado")
            render_template('Registro_usuarios_interfaz_administrador.html')
        else:   
            # Obtener el ID del usuario autenticado desde la sesión
            id_usuario = session.get('id_usuario')
            print(f"ID del usuario autenticado: {id_usuario}")
            
            # Verifica si id_usuario es None o inválido
            if id_usuario is None:
                print("ID del usuario no se encontró en la sesión")
                return render_template('Registro_tareas_interfaz_administrador.html')    
             
            # Insertar usuarios a la tabla usuarios        
            cursor.execute("INSERT INTO usuarios(Nombres,Apellidos,Email,Nombre_usuario,Contraseña,Rol) VALUES(%s,%s,%s,%s,%s,%s)",(nombres_usuario,apellidos_usuario,email_usuario,nombre_usuario,contraseña,rol))
            db.commit()
            print("¡Usuario registrado!")                 
            return redirect(url_for('RegistrarUsuario_interfaz_administrador'))            
    return render_template('Registro_usuarios_interfaz_administrador.html') 

@app.route('/Registro-tareas-interfaz-administador',methods=['GET' , 'POST'])  
def RegistrarTarea_interfaz_administrador():
    # Obtén el nombre de usuario de la sesión
    nombre_usuario = session.get('nombre_usuario')
    
    # Verifica si el usuario está autenticado
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    print(f"Nombre de usuario recuperado de la sesión: {nombre_usuario}") 
    
    db = get_db_connection()
    cursor = db.cursor()
    
    if request.method == 'POST':
        nombre_tarea = request.form.get('nombre_tarea')
        fecha_inicio = request.form.get('fecha_inicio')         
        fecha_fin = request.form.get('fecha_fin') 
        estado = request.form.get('estado')    
        print(f"Nombre de tarea: {nombre_tarea}, Fecha de inicio: {fecha_inicio}, Fecha de fin: {fecha_fin}, Estado: {estado}")     
        
        # Verificar que el nombre de la tarea no este registrado
        cursor.execute('SELECT * FROM tareas WHERE Nombre = %s ',(nombre_tarea,))
        Existe = cursor.fetchone()
        
        if Existe:                        
            print("¡¡¡El nombre de la tarea ya esta registrado!!!")
            return render_template('Registro_tareas_interfaz_administrador.html')
        else:
            # Obtener el ID del usuario autenticado desde la sesión
            id_usuario = session.get('id_usuario')
            print(f"ID del usuario autenticado: {id_usuario}")
            
            # Verifica si id_usuario es None o inválido
            if id_usuario is None:
                print("ID del usuario no se encontró en la sesión")
                return render_template('Registro_tareas_interfaz_administrador.html')

            # Insertar la nueva tarea en la tabla tareas con el ID del usuario        
            cursor.execute("INSERT INTO tareas(Nombre,Fecha_Inicio,Fecha_Fin,Estado,ID_Usuario) VALUES(%s,%s,%s,%s,%s)",(nombre_tarea,fecha_inicio,fecha_fin,estado,id_usuario))
            db.commit()
            print("¡Tarea registrada con exito!") 
            return redirect(url_for('RegistrarTarea_interfaz_administrador'))                           
    return render_template('Registro_tareas_interfaz_administrador.html')

@app.route('/Usuario')
def Interfaz_usuario():
    nombre_usuario = session.get('nombre_usuario') 
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))   
    
    print(f"Nombre de usuario recuperado de la sesión: {nombre_usuario}")    
          
    return render_template('Interfaz_usuario.html', nombre_usuario=nombre_usuario) 

@app.route('/Listar_tareas-usuario')
def Usuario_tareas():
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Recupera el ID del usuario autenticado
    cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Nombre_usuario = %s", (nombre_usuario,))
    usuario = cursor.fetchone()

    # Verifica si el usuario fue encontrado
    if usuario is None:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('IngresoUsuario'))

    id_usuario = usuario['ID_Usuario']

    # Consulta para obtener las tareas del usuario autenticado
    cursor.execute("SELECT * FROM tareas WHERE ID_Usuario = %s", (id_usuario,))
    tareas = cursor.fetchall()

    # Renderiza la tabla con las tareas del usuario
    return render_template('Interfaz_usuario.html', tareas=tareas, nombre_usuario=nombre_usuario)

@app.route('/borrar_tarea_usuario/<int:id>', methods=['GET'])
def borrar_tarea_usuario(id):
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    
    # Configura el cursor para usar un cursor de diccionario
    cursor = db.cursor(dictionary=True)

    # Recupera el ID del usuario autenticado
    cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Nombre_usuario = %s", (nombre_usuario,))
    usuario = cursor.fetchone()

    # Verifica si el usuario fue encontrado
    if usuario is None:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('IngresoUsuario'))

    id_usuario = usuario['ID_Usuario']

    # Verifica si la tarea le pertenece al usuario
    cursor.execute("SELECT * FROM tareas WHERE ID_Tarea = %s AND ID_Usuario = %s", (id, id_usuario))
    tarea = cursor.fetchone()
    
    # Si la tarea no existe o no pertenece al usuario, redirige con error
    if not tarea or tarea['ID_Usuario'] != id_usuario:
        flash('Tarea no encontrada o no pertenece al usuario', 'error')
        return redirect(url_for('Usuario_tareas'))

    # Ejecuta la consulta para borrar la tarea con el ID especificado
    cursor.execute("DELETE FROM tareas WHERE ID_Tarea = %s", (id,))
    db.commit()  # Confirma la transacción
    
    # Mensaje de depuración
    print(f"Tarea con ID {id} ha sido eliminada por el usuario con ID {id_usuario}.")

    # Redirige a la página de lista de tareas del usuario
    return redirect(url_for('Usuario_tareas'))

@app.route('/editar_tarea_usuario/<int:id>', methods=['GET', 'POST'])
def editar_tarea_usuario(id):
    # Verifica si el usuario está autenticado
    nombre_usuario = session.get('nombre_usuario')
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))

    # Obtén una conexión a la base de datos
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Recupera el ID del usuario autenticado
    cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Nombre_usuario = %s", (nombre_usuario,))
    usuario = cursor.fetchone()

    # Verifica si el usuario fue encontrado
    if usuario is None:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('IngresoUsuario'))

    id_usuario = usuario['ID_Usuario']

    # Verifica si la tarea le pertenece al usuario
    cursor.execute("SELECT * FROM tareas WHERE ID_Tarea = %s AND ID_Usuario = %s", (id, id_usuario))
    tarea = cursor.fetchone()
    
    # Si la tarea no existe o no pertenece al usuario, redirige con error
    if not tarea:
        flash('Tarea no encontrada o no pertenece al usuario', 'error')
        return redirect(url_for('Usuario_tareas'))

    # Si el método es POST, actualiza la tarea con los datos proporcionados
    if request.method == 'POST':
        # Obtén los datos del formulario
        nombre = request.form.get('nombre')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        estado = request.form.get('estado')

        # Mensaje de depuración para verificar los valores antes de la actualización
        print(f"Actualizando tarea con ID {id}: Nombre = {nombre}, Fecha_Inicio = {fecha_inicio}, Fecha_Fin = {fecha_fin}, Estado = {estado}")

        # Ejecuta la consulta para actualizar la tarea
        cursor.execute(
            "UPDATE tareas SET Nombre = %s, Fecha_Inicio = %s, Fecha_Fin = %s, Estado = %s WHERE ID_Tarea = %s AND ID_Usuario = %s",
            (nombre, fecha_inicio, fecha_fin, estado, id, id_usuario)
        )

        # Confirma la transacción
        db.commit()

        # Mensaje de depuración para confirmar el éxito de la actualización
        print(f"Tarea con ID {id} ha sido actualizada por el usuario con ID {id_usuario}.")

        # Redirige a la lista de tareas del usuario
        return redirect(url_for('Usuario_tareas'))

    # Si el método es GET, muestra el formulario de edición de la tarea
    return render_template('Modificar_tarea_usuario.html', tarea=tarea)

@app.route('/Registro_tareas',methods=['GET' , 'POST'])  
def RegistrarTarea():
    # Obtén el nombre de usuario de la sesión
    nombre_usuario = session.get('nombre_usuario')
    
    # Verifica si el usuario está autenticado
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    db = get_db_connection()
    cursor = db.cursor()
    
    if request.method == 'POST':
        nombre_tarea = request.form.get('nombre_tarea')
        fecha_inicio = request.form.get('fecha_inicio')         
        fecha_fin = request.form.get('fecha_fin') 
        estado = request.form.get('estado')    
        print(f"Nombre de tarea: {nombre_tarea}, Fecha de inicio: {fecha_inicio}, Fecha de fin: {fecha_fin}, Estado: {estado}")     
        
        # Verificar que el nombre de la tarea no este registrado
        cursor.execute('SELECT * FROM tareas WHERE Nombre = %s ',(nombre_tarea,))
        Existe = cursor.fetchone()
        
        if Existe:                        
            print("¡¡¡El nombre de la tarea ya esta registrado!!!")
            return render_template('Registro_tareas_interfaz_usuario.html')
        else:
            # Obtener el ID del usuario autenticado desde la sesión
            id_usuario = session.get('id_usuario')
            
            # Verifica si id_usuario es None o inválido
            if id_usuario is None:
                print("ID del usuario no se encontró en la sesión")
                return render_template('Registro_tareas_interfaz_administrador.html')
            
            # Insertar la nueva tarea en la tabla tareas con el ID del usuario       
            cursor.execute("INSERT INTO tareas(Nombre,Fecha_Inicio,Fecha_Fin,Estado,ID_Usuario) VALUES(%s,%s,%s,%s,%s)",(nombre_tarea,fecha_inicio,fecha_fin,estado,id_usuario))
            db.commit()
            print("¡Tarea registrada con exito!")        
            return redirect(url_for('RegistrarTarea'))                    
    return render_template('Registro_tareas_interfaz_usuario.html')

@app.route('/Cambiar_contrasena_administrador', methods=['GET', 'POST'])
def cambiar_contrasena_admin():
    # Obtén el nombre de usuario de la sesión
    nombre_usuario = session.get('nombre_usuario')
    
    # Verifica si el usuario está autenticado
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')

        # Verifica que la nueva contraseña y la confirmación coincidan
        if nueva_contrasena != confirmar_contrasena:
            # Manejar el caso en que las contraseñas no coincidan
            return "Las contraseñas no coinciden. Inténtalo de nuevo."
        
        # Aquí debes implementar la lógica para verificar la contraseña actual con la almacenada en la base de datos
        # Una vez verificada, puedes actualizar la contraseña directamente en la base de datos
        db = get_db_connection()
        cursor = db.cursor()

        # Actualiza la contraseña en la base de datos
        cursor.execute("UPDATE usuarios SET Contraseña = %s WHERE Nombre_usuario = %s", (nueva_contrasena, nombre_usuario))
        db.commit()
        print("¡Contraseña cambiada con exito!")
        db.close()

        # Redirige a algún lugar apropiado después de cambiar la contraseña
        return redirect(url_for('Interfaz_administrador'))

    return render_template('Cambiar_contraseña_admin.html')

@app.route('/Cambiar_contrasena_usuario', methods=['GET', 'POST'])
def cambiar_contrasena_usuario():
    # Obtén el nombre de usuario de la sesión
    nombre_usuario = session.get('nombre_usuario')
    
    # Verifica si el usuario está autenticado
    if nombre_usuario is None:
        # Redirige a la página de inicio de sesión si no está autenticado
        return redirect(url_for('IngresoUsuario'))
    
    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')

        # Verifica que la nueva contraseña y la confirmación coincidan
        if nueva_contrasena != confirmar_contrasena:
            # Manejar el caso en que las contraseñas no coincidan
            return "Las contraseñas no coinciden. Inténtalo de nuevo."
        
        # Aquí debes implementar la lógica para verificar la contraseña actual con la almacenada en la base de datos
        # Una vez verificada, puedes actualizar la contraseña directamente en la base de datos
        db = get_db_connection()
        cursor = db.cursor()

        # Actualiza la contraseña en la base de datos
        cursor.execute("UPDATE usuarios SET Contraseña = %s WHERE Nombre_usuario = %s", (nueva_contrasena, nombre_usuario))
        db.commit()
        print("¡Contraseña cambiada con exito!")
        db.close()

        # Redirige a algún lugar apropiado después de cambiar la contraseña
        return redirect(url_for('Interfaz_usuario'))

    return render_template('Cambiar_contraseña_usuario.html')

@app.route('/Salir')  
def Salir():   
    session.pop("nombre_usuario", None)
    print("Sesión cerrada y nombre de usuario eliminado.")
    
    return redirect(url_for('IngresoUsuario')) 

# No almacenar el cache de la pagina
@app.after_request
def add_header(response):    
    response.headers['Cache-Control'] = 'no-cache,no-store,must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = 0    
    return response      

if __name__ == '__main__':
    app.run(debug=True)  
    app.add_url_rule('/',view_func=Inicio)   
    app.add_url_rule('/Registro',view_func=RegistrarUsuario) 
    app.add_url_rule('/Ingreso',view_func=IngresoUsuario)   
    app.add_url_rule('/Administrador',view_func=Interfaz_administrador)
    app.add_url_rule('/Listar_usuarios',view_func=Mostrar_usuarios)
    app.add_url_rule('/borrar_usuario',view_func=borrar_usuario)
    app.add_url_rule('/editar_usuario',view_func=editar_usuario)
    app.add_url_rule('/Listar_tareas',view_func=Mostrar_tareas)
    app.add_url_rule('/borrar_tarea',view_func=borrar_tarea)
    app.add_url_rule('/editar_tarea',view_func=editar_tarea)
    app.add_url_rule('/Registro-usuarios-interfaz-administrador',view_func=RegistrarUsuario_interfaz_administrador)
    app.add_url_rule('/Registro-tareas-interfaz-administador',view_func=RegistrarTarea_interfaz_administrador)
    app.add_url_rule('/Usuario',view_func=Interfaz_usuario)
    app.add_url_rule('/Listar_tareas-usuario',view_func=Usuario_tareas)
    app.add_url_rule('/borrar_tarea_usuario',view_func=borrar_tarea_usuario)
    app.add_url_rule('/editar_tarea_usuario',view_func=editar_tarea_usuario)
    app.add_url_rule('/Registro_tareas',view_func=RegistrarTarea) 
    app.add_url_rule('/Cambiar_contrasena_administrador',view_func=cambiar_contrasena_admin) 
    app.add_url_rule('/Cambiar_contrasena_usuario',view_func=cambiar_contrasena_usuario) 
    app.add_url_rule('/Salir',view_func=Salir)       
