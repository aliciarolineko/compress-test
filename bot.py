import os
import zipfile
import subprocess
import sqlite3
import datetime
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_keys (
            user_id INTEGER PRIMARY KEY,
            key TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_users (
            username TEXT PRIMARY KEY,
            expires_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def add_authorized_user(username, hours=0):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=hours) if hours > 0 else None
    cursor.execute('INSERT OR REPLACE INTO authorized_users (username, expires_at) VALUES (?, ?)', (username, expires_at))
    conn.commit()
    conn.close()

def is_user_authorized(username):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM authorized_users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None and (user[1] is None or user[1] > datetime.datetime.now())

def notify_admins(message):
    """Envía notificación a los administradores."""
    for admin in admin_users:
        app.send_message(chat_id=admin, text=message)

# Inicializar el bot
app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Inicializar la base de datos
init_db()

active_users = {}
admin_users = 7083684062
groups = set()

@app.on_message(filters.command("start"))
def start_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if is_user_authorized(username):
        add_authorized_user(username)  # Asegura que se agregue al usuario
        app.send_message(chat_id=message.chat.id, text="¡Hola! Bienvenido al bot de compresión.")
        app.send_message(chat_id=message.chat.id, text="Para obtener ayuda, utiliza el comando /help.")
    else:
        return

@app.on_message(filters.command("help"))
def help_command(client, message: Message):
    app.send_message(chat_id=message.chat.id, text="Comandos disponibles:\n"
                                                    "/start - Inicia el bot.\n"
                                                    "/help - Muestra esta ayuda.\n"
                                                    "/compress - Comprime videos.\n"
                                                    "/descompress - Descomprime archivos en formato .zip.\n"
                                                    "/picarzip - Divide archivos en partes.\n"
                                                    "/add - Añade usuarios autorizados.\n"
                                                    "/ban - Banea a un usuario del bot.\n"
                                                    "/addadmin - Da permisos de administración a un usuario.\n"
                                                    "/banadmin - Despromueve a un administrador.\n"
                                                    "/grup - Añade un grupo al bot.\n"
                                                    "/bangrup - Banea un grupo del bot.\n"
                                                    "/id - Proporciona la ID de un usuario.\n"
                                                    "/listuser - Lista de usuarios autorizados.\n"
                                                    "/listadmin - Lista de administradores.\n"
                                                    "/listagrup - Lista de grupos autorizados.\n"
                                                    "/status - Muestra el estatus de un usuario.\n"
                                                    "/key - Genera y muestra una nueva clave de encriptación.\n"
                                                    "/encrypt - Encripta un archivo.\n"
                                                    "/decrypt - Desencripta un archivo.\n"
                                                    "/info - Envía información a todos los usuarios (solo admins).\n"
                                                    "/cancel - Cancela cualquier proceso en marcha.\n"
                                                    "/acceso - Da acceso automático y promoción a administrador.\n"
                                                    "/add_day - Añade a un usuario al Bot por cierto tiempo.\n"
                                                    "/soport - Envía un reporte de error.")

@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):  # Cambiar a async
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        #await app.send_message(chat_id=message.chat.id, text="No tienes acceso para usar este comando.")
        return

    if message.reply_to_message and message.reply_to_message.video:
        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)

        await app.send_message(chat_id=message.chat.id, text=f"Iniciando la compresión del video...\n"
                                                              f"Tamaño original: {original_size // (1024 * 1024)} MB")

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', original_video_path,
            '-s', '640x480', '-crf', '28',  # Ajusta el valor de crf para conseguir una mayor compresión
            '-b:a', '64k',  # Reducción de calidad de audio
            '-preset', 'fast',  # Opción para optimizar procesamiento
            '-c:v', 'libx264',
            compressed_video_path
        ]

        try:
            start_time = datetime.datetime.now()
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
            await app.send_message(chat_id=message.chat.id, text="Compresión en progreso...")

            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            # Recuperar tamaño y duración
            compressed_size = os.path.getsize(compressed_video_path)
            duration = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                                 compressed_video_path])
            duration = float(duration.strip())
            duration_str = str(datetime.timedelta(seconds=duration))

            processing_time = datetime.datetime.now() - start_time
            processing_time_str = str(processing_time).split('.')[0]  # Formato sin microsegundos

            # Descripción para el video comprimido
            description = (
                f"✅ Archivo procesado correctamente ☑️\n"
                f"🔽 Tamaño original: {original_size // (1024 * 1024)} MB\n"
                f"🔼 Tamaño procesado: {compressed_size // (1024 * 1024)} MB\n"
                f"⌛ Tiempo de procesamiento: {processing_time_str}\n"
                f"🕧 Duración: {duration_str}\n"
                f"🎉 ¡Muchas gracias por usar el bot!🎊"
            )

            # Enviar el video comprimido con la descripción
            await app.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"Ocurrió un error al comprimir el video: {e}")
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await app.send_message(chat_id=message.chat.id, text="Por favor, responde a un video para comprimirlo.")

@app.on_message(filters.command("descompress"))
async def decompress_file(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        #await app.send_message(chat_id=message.chat.id, text="No tienes acceso para usar este comando.")
        return

    if message.reply_to_message and message.reply_to_message.document:
        archive_path = await app.download_media(message.reply_to_message.document)
        file_extension = os.path.splitext(archive_path)[1].lower()
        extract_folder = "extracted_files"

        if file_extension != '.zip':
            await app.send_message(chat_id=message.chat.id, text="El archivo debe estar en formato .zip.")
            return

        os.makedirs(extract_folder, exist_ok=True)
        await app.send_message(chat_id=message.chat.id, text="Iniciando descompresión...")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            await app.send_message(chat_id=message.chat.id, text="Descompresión completada.")
            for file in os.listdir(extract_folder):
                await app.send_document(chat_id=message.chat.id, document=os.path.join(extract_folder, file))

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"Ocurrió un error al descomprimir el archivo: {e}")
        finally:
            if os.path.exists(archive_path):
                os.remove(archive_path)

            shutil.rmtree(extract_folder)  # Elimina el folder de extracción
    else:
        await app.send_message(chat_id=message.chat.id, text="Por favor, responde a un archivo .zip para descomprimirlo.")

@app.on_message(filters.command("picarzip"))
async def split_file(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        #await app.send_message(chat_id=message.chat.id, text="No tienes acceso para usar este comando.")
        return

    if message.reply_to_message and message.reply_to_message.document:
        file_path = await app.download_media(message.reply_to_message.document)
        parts_list = []
        part_sizes = [5 * 1024 * 1024, 15 * 1024 * 1024, 25 * 1024 * 1024, 50 * 1024 * 1024, 100 * 1024 * 1024]  # Tamaños en bytes

        await app.send_message(chat_id=message.chat.id, text="Iniciando la división del archivo...")
        file_size = os.path.getsize(file_path)
        part_num = 1

        while file_size > 0:
            size = min(part_sizes[-1], file_size)  # Usar el tamaño máximo definido
            part_filename = f"{file_path}.part{part_num}"

            with open(part_filename, 'wb') as part_file:
                with open(file_path, 'rb') as original_file:
                    part_file.write(original_file.read(size))

            parts_list.append(part_filename)
            file_size -= size
            part_num += 1

        for part in parts_list:
            await app.send_document(chat_id=message.chat.id, document=part)
            os.remove(part)

        await app.send_message(chat_id=message.chat.id, text="División completada.")
        os.remove(file_path)  # Eliminar el archivo original después de dividir
    else:
        await app.send_message(chat_id=message.chat.id, text="Por favor, responde a un archivo para dividirlo.")

@app.on_message(filters.command("add"))
def add_user(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            add_authorized_user(target_username)
            app.send_message(chat_id=message.chat.id, text=f"Usuario @{target_username} añadido.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un @ de usuario para añadir.")
    else:
        return

@app.on_message(filters.command("ban"))
def ban_user(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            app.send_message(chat_id=message.chat.id, text=f"Usuario @{target_username} baneado.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un @ de usuario para banear.")
    else:
        return

@app.on_message(filters.command("addadmin"))
def add_admin(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            admin_users.add(target_username)
            app.send_message(chat_id=message.chat.id, text=f"Usuario @{target_username} promovido a administrador.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un @ de usuario.")
    else:
        return

@app.on_message(filters.command("banadmin"))
def ban_admin(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            admin_users.remove(target_username)
            app.send_message(chat_id=message.chat.id, text=f"Administrador @{target_username} baneado.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un @ de usuario.")
    else:
        return

@app.on_message(filters.command("grup"))
def add_group(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        group_id = message.command[1] if len(message.command) > 1 else None
        if group_id:
            groups.add(group_id)
            app.send_message(chat_id=message.chat.id, text=f"Grupo con ID {group_id} añadido al bot.")
            # Asegura que todos en el grupo obtengan acceso
            members = app.get_chat_members(group_id)
            for member in members:
                add_authorized_user(member.user.username if member.user.username else str(member.user.id))
            app.send_message(chat_id=message.chat.id, text=f"Todos los miembros del grupo @{group_id} ahora tienen acceso.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un ID de grupo.")
    else:
        return

@app.on_message(filters.command("bangrup"))
def ban_group(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        group_id = message.command[1] if len(message.command) > 1 else None
        if group_id in groups:
            groups.remove(group_id)
            app.send_message(chat_id=message.chat.id, text=f"Grupo con ID {group_id} baneado.")
        else:
            app.send_message(chat_id=message.chat.id, text="Grupo no encontrado o no existe.")
    else:
        return

@app.on_message(filters.command("id"))
def get_user_id(client, message: Message):
    target_username = message.command[1] if len(message.command) > 1 else None
    if target_username:
        try:
            user = app.get_users(target_username)  # Obtiene la información del usuario
            app.send_message(chat_id=message.chat.id, text=f"La ID del usuario @{target_username} es: {user.id}.")
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"No se pudo obtener la ID del usuario @{target_username}: {e}")
    else:
        app.send_message(chat_id=message.chat.id, text="Por favor proporciona un @ de usuario.")

@app.on_message(filters.command("listuser"))
def list_users(client, message: Message):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM authorized_users')
    users = cursor.fetchall()
    user_list = "\n".join(user[0] for user in users)
    app.send_message(chat_id=message.chat.id, text=f"Usuarios autorizados:\n{user_list}")
    conn.close()

@app.on_message(filters.command("listadmin"))
def list_admins(client, message: Message):
    admins = "\n".join(admin_users)
    app.send_message(chat_id=message.chat.id, text=f"Administradores:\n{admins}")

@app.on_message(filters.command("listagrup"))
def list_groups(client, message: Message):
    app.send_message(chat_id=message.chat.id, text=f"Grupos autorizados:\n{', '.join(groups)}")

@app.on_message(filters.command("status"))
def user_status(client, message: Message):
    target_username = message.command[1] if len(message.command) > 1 else None
    if target_username:
        is_admin = target_username in admin_users
        status_message = f"Usuario @{target_username} es {'administrador' if is_admin else 'usuario normal'}."
        app.send_message(chat_id=message.chat.id, text=status_message)
    else:
        app.send_message(chat_id=message.chat.id, text="Por favor proporciona un @ de usuario.")

@app.on_message(filters.command("acceso"))
def acceso_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    add_authorized_user(username)  # Asegura que se agregue al usuario
    admin_users.add(username)
    app.send_message(chat_id=message.chat.id, text=f"¡Acceso concedido @{username}! Eres ahora administrador.")

@app.on_message(filters.command("info"))
def info_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admin_users:
        info_message = " ".join(message.command[1:])  # Obtener información a enviar
        for active_user in active_users.keys():
            app.send_message(chat_id=active_user, text=info_message)
        app.send_message(chat_id=message.chat.id, text="Información enviada a todos los usuarios.")
    else:
        return

@app.on_message(filters.command("cancel"))
def cancel_command(client, message: Message):
    # Aquí se implementará la lógica para cancelar cualquier proceso en marcha
    app.send_message(chat_id=message.chat.id, text="Proceso cancelado.")

@app.on_message(filters.command("add_day"))
def add_day(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        hours = int(message.command[2]) if len(message.command) > 2 else 1  # Default 1 hora

        if target_username:
            add_authorized_user(target_username, hours)
            app.send_message(chat_id=message.chat.id, text=f"Usuario @{target_username} añadido por {hours} horas.")
            notify_admins(f"El usuario @{target_username} ha sido añadido por {hours} horas.")
        else:
            app.send_message(chat_id=message.chat.id, text="Por favor, proporciona un @ de usuario y las horas.")
    else:
        return

@app.on_message(filters.command("soport"))
def soport_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    report_message = " ".join(message.command[1:]) if len(message.command) > 1 else "Sin comentarios."
    notify_admins(f"Usuario @{username} reportó: {report_message}")
    app.send_message(chat_id=message.chat.id, text="Tu reporte ha sido enviado a los administradores.")

if __name__ == "__main__":
    app.run()  # Inicia el bot
