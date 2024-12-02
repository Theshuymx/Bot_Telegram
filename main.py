import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import yt_dlp
import os

# Configuración del logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Comando /start
async def start(update: Update, context):
    welcome_message = (
        "¡Hola! 👋 Bienvenido al bot de descarga de videos y música. 🎥🎶\n\n"
        "Solo envíame un enlace de video (por ejemplo, de YouTube o Twitter) "
        "y te preguntaré si deseas descargarlo como video o MP3, y después elegir la calidad. ¡Disfruta! 😊\n\n"
        "Este bot fue creado por @shuymx."
    )
    await update.message.reply_text(welcome_message)

# Manejo de mensajes con enlaces
async def handle_message(update: Update, context):
    url = update.message.text
    if "http" in url:
        context.user_data['url'] = url
        keyboard = [
            [InlineKeyboardButton("Descargar Video", callback_data="video")],
            [InlineKeyboardButton("Descargar MP3", callback_data="mp3")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("¿Cómo deseas descargarlo?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Por favor, envíame un enlace válido.")

# Manejo de selección de tipo de descarga
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_url = context.user_data.get('url')
    download_type = query.data

    if user_url:
        await query.message.reply_text(f"Descargando como {download_type.upper()}...")
        try:
            file_path = download_media(user_url, download_type)

            # Enviar el archivo descargado
            with open(file_path, 'rb') as media_file:
                if download_type == "video":
                    await query.message.reply_video(media_file)
                elif download_type == "mp3":
                    await query.message.reply_audio(media_file)

            os.remove(file_path)  # Limpiar archivo local
            await query.message.reply_text("¡Gracias por usar este bot creado por shuymx!")
            await query.message.reply_text("Este bot 🤖 está en beta. Cualquier error o sugerencia, házmelo saber @shuymx.")
        except Exception as e:
            logger.error(f"Error al descargar el archivo: {e}")
            await query.message.reply_text("Hubo un error al procesar tu solicitud.")
    else:
        await query.message.reply_text("Por favor, envíame primero un enlace válido.")

# Descarga de contenido usando yt-dlp
def download_media(url, download_type):
    ydl_opts = {
        'quiet': True,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'geo-bypass': True,
    }

    if download_type == "video":
        ydl_opts['format'] = 'mp4'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Función principal para mantener el bot corriendo
def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Usar el token desde las variables de entorno

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button, pattern="^(video|mp3)$"))

    # Iniciar el bot en un bucle infinito
    try:
        application.run_polling()  # run_polling se encarga de mantener el bot corriendo
        logger.info("El bot está funcionando. Envía mensajes o comandos para probarlo.")
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()
