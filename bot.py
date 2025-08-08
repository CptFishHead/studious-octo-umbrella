from __future__ import annotations
import asyncio
import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from app.settings import load_settings
from app.utils import normalize_instagram_url, extract_shortcode, is_allowed, download_file
from app.instagram import InstagramClient
from app.models import NotVideo, PrivateOrNotFound, FileTooLarge, ForbiddenUser

settings = load_settings()
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("tg-ig-bot")

HELP_TEXT = (
    "Пришлите ссылку на ваш пост/риелс Instagram. "
    "Бот получит видео через Instagram Graph API и отправит в чат.\n"
    "Только ваш контент. Если файл больше лимита Telegram — пришлю ссылку.\n"
)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Это бот-посредник Instagram → Telegram.\n" + HELP_TEXT)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_allowed(user_id, settings.allowed_user_ids):
        raise ForbiddenUser("You are not allowed to use this bot")

    text = update.message.text or ""
    urls = [e.url for e in (update.message.entities or []) if e.type == 'url']
    candidate = urls[0] if urls else text.strip()
    if not candidate:
        await update.message.reply_text("Дайте корректный URL поста/риелса Instagram")
        return

    try:
        permalink = normalize_instagram_url(candidate)
        _ = extract_shortcode(permalink)
    except Exception:
        await update.message.reply_text("Дайте корректный URL поста/риелса Instagram")
        return

    await update.message.chat.send_action(ChatAction.TYPING)
    client = InstagramClient(settings.IG_USER_ID, settings.IG_ACCESS_TOKEN)
    try:
        media = await client.find_media_by_permalink(permalink)
        if media.media_type not in {"VIDEO", "REEL"} or not media.video_url:
            raise NotVideo("This media is not a video/reel")

        max_bytes = settings.MAX_FILE_MB * 1024 * 1024
        try:
            file_path = await download_file(media.video_url, max_bytes=max_bytes)
        except FileTooLarge as e:
            await update.message.reply_text(
                f"Файл слишком большой (>{e.limit_mb:.1f}MB). Ссылка на видео: {media.video_url}"
            )
            return

        await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
        with open(file_path, "rb") as f:
            await update.message.reply_video(video=f, caption=media.permalink or permalink)
    except ForbiddenUser:
        await update.message.reply_text("Доступ запрещён")
    except NotVideo:
        await update.message.reply_text("Это не видео/риелс или отсутствует video_url")
    except PrivateOrNotFound:
        await update.message.reply_text("Медиа не найдено среди ваших публикаций или доступ ограничен")
    except Exception:
        logger.exception("Unhandled error")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    finally:
        await client.aclose()

async def main():
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(MessageHandler(filters.TEXT | filters.Entity("url"), handle_text))

    if settings.TELEGRAM_WEBHOOK_URL:
        logger.info("Starting webhook mode at %s", settings.TELEGRAM_WEBHOOK_URL)
        await app.run_webhook(
            listen=settings.HOST,
            port=settings.PORT,
            url_path=settings.TELEGRAM_BOT_TOKEN,
            webhook_url=f"{settings.TELEGRAM_WEBHOOK_URL}/{settings.TELEGRAM_BOT_TOKEN}",
        )
    else:
        logger.info("Starting polling mode")
        await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(main())
