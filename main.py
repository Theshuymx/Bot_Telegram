import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# Configuración del logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Función para manejar el comando /start
async def start(update: Update, context):
    welcome_message = (
        "¡Hola! 👋 Soy un bot para descargar videos en formato MP4 y extraer su audio. 🎥🎶\n\n"
        "Envíame un enlace de YouTube o X, y lo descargaré para ti. Luego podrás elegir si también quieres el audio.\n\n"
        "Este bot fue creado por @shuymx."
    )
    await update.message.reply_text(welcome_message)

# Función para manejar enlaces enviados por los usuarios
async def handle_message(update: Update, context):
    url = update.message.text.strip()
    if "youtube.com" in url or "youtu.be" in url or "x.com" in url:
        await update.message.reply_text("⏳ Procesando tu solicitud, por favor espera...")
        try:
            file_path = download_video_as_mp4(url)
            if file_path:
                await update.message.reply_text("✅ Video descargado exitosamente. Enviando archivo...")
                with open(file_path, "rb") as video_file:
                    await update.message.reply_video(video_file)
                await update.message.reply_text(
                    "🎉 ¡Listo! Gracias por usar este bot. 😊\n\n"
                    "🤖 Este bot está en beta, cualquier error o sugerencia hazmelo saber en @shuymx."
                )
                
                # Guardar la ruta del video en el contexto para el audio
                context.user_data["video_path"] = file_path

                # Preguntar si quiere el audio
                keyboard = [
                    [InlineKeyboardButton("Sí, quiero el audio 🎶", callback_data="audio")],
                    [InlineKeyboardButton("No, gracias", callback_data="no_audio")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("¿Quieres el audio del video?", reply_markup=reply_markup)
            else:
                await update.message.reply_text("❌ No se pudo descargar el video.")
        except Exception as e:
            logger.error(f"Error al descargar el video: {e}")
            await update.message.reply_text("❌ Hubo un error al procesar tu solicitud.")
    else:
        await update.message.reply_text("Por favor, envíame un enlace válido de YouTube o X.")

# Función para manejar la respuesta sobre el audio
async def handle_audio_request(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_choice = query.data

    if user_choice == "audio":
        video_path = context.user_data.get("video_path")
        if video_path:
            await query.message.reply_text("⏳ Extrayendo el audio, por favor espera...")
            try:
                audio_path = convert_to_mp3(video_path)
                with open(audio_path, "rb") as audio_file:
                    await query.message.reply_audio(audio_file)
                await query.message.reply_text(
                    "🎉 ¡Audio enviado! Gracias por usar este bot. 😊\n\n"
                    "🤖 Este bot está en beta, cualquier error o sugerencia hazmelo saber en @shuymx."
                )
                
                # Limpiar archivos después de enviarlos
                os.remove(audio_path)
                os.remove(video_path)
            except Exception as e:
                logger.error(f"Error al extraer el audio: {e}")
                await query.message.reply_text("❌ Hubo un error al extraer el audio.")
        else:
            await query.message.reply_text("❌ No se encontró el video para extraer el audio.")
    elif user_choice == "no_audio":
        await query.message.reply_text(
            "👌 Entendido, Gracias por usar este bot. 😊\n\n"
            "🤖 Este bot está en beta, cualquier error o sugerencia hazmelo saber en @shuymx."
        )

# Función para descargar videos en formato MP4
def download_video_as_mp4(url):
    ydl_opts = {
        "format": "mp4",  # Descargar en formato MP4
        "outtmpl": "downloads/%(title)s.%(ext)s",  # Ruta y nombre del archivo
        "quiet": True,
        "geo-bypass": True,
    }
    os.makedirs("downloads", exist_ok=True)  # Crear carpeta si no existe

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Función para convertir un video a MP3
def convert_to_mp3(video_path):
    audio_path = video_path.replace(".mp4", ".mp3")
    os.system(f"ffmpeg -i \"{video_path}\" -vn -ab 192k -ar 44100 -y \"{audio_path}\"")
    return audio_path

# Función principal para ejecutar el bot
def main():
    TELEGRAM_TOKEN = "TELEGRAM_TOKEN"  # Reemplaza con tu token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_audio_request, pattern="^(audio|no_audio)$"))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
