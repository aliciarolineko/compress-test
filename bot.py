import os
from pyrogram import Client, filters
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.video | filters.document)
async def video_handler(client, message):
    temp_dir = "server/tempcompress"
    try:
        # Crear carpeta temporal
        os.makedirs(temp_dir, exist_ok=True)
        
        # Descargar el archivo
        file_path = await message.download(file_name=temp_dir)
        
        # Convertir el video
        output_path = os.path.join(temp_dir, "output.mkv")
        clip = VideoFileClip(file_path)
        clip_resized = clip.resize(height=480)
        clip_resized.write_videofile(output_path, fps=20, codec="libx264")
        
    except Exception as e:
        await message.reply_text("Error")
    else:
        # Enviar el video convertido si no hubo errores
        await message.reply_video(video=output_path)
    finally:
        # Borrar archivos y carpeta temporal
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)

app.run()
