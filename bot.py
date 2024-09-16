import os
from telethon import TelegramClient, events
from dotenv import load_dotenv
import ffmpeg

# Cargar variables de entorno
load_dotenv()
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# Crear cliente de Telegram
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage)
async def handler(event):
    if event.message.media:
        try:
            # Enviar mensaje de progreso: Descargando el archivo
            await event.reply('Descargando el archivo...')
            
            # Descargar el archivo
            file_path = await client.download_media(event.message.media)
            new_file_path = file_path.rsplit('.', 1)[0] + '.mkv'

            # Enviar mensaje de progreso: Convirtiendo el archivo
            await event.reply('Convirtiendo el archivo...')
            
            # Convertir el archivo a MKV con la altura de 480 píxeles y la anchura proporcional
            ffmpeg.input(file_path).output(new_file_path, vf='scale=-1:480', r=20, ar=48000).run()

            # Enviar mensaje de progreso: Enviando el archivo
            await event.reply('Enviando el archivo...')
            
            # Enviar el nuevo archivo al chat
            await client.send_file(event.chat_id, new_file_path)

            # Borrar los archivos
            os.remove(file_path)
            os.remove(new_file_path)
        except Exception as e:
            await event.reply('Falló')
            print(f'Error: {e}')

# Iniciar el cliente
client.run_until_disconnected()
