# hooks/editor_reaction.py
import aiohttp
import asyncio
import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)

class EditorReaction:
    """Хук для обработки нажатий кнопок в редакторе."""
    
    WEBHOOK_PORT = 8082
    
    def __init__(self):
        self.bot_token = os.getenv('EDITOR_API')  # Токен для бота редактора
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов."""
        self.app.router.add_post('/webhook/editor', self.editor_webhook)
        self.app.router.add_get('/health', self.health)
    
    async def editor_webhook(self, request):
        """Принимает нажатия кнопок от редактора."""
        try:
            update = await request.json()
            logger.info(f"📩 Editor hook: получен вебхук")
            
            if "callback_query" in update:
                callback = update["callback_query"]
                callback_data = callback.get("data", "")
                message = callback.get("message", {})
                message_id = message.get("message_id")
                
                # Определяем какая кнопка нажата
                if callback_data.startswith("btn_add_"):
                    url = "https://n8n-tg-marcell88.amvera.io/webhook/29b7a936-c6c4-4f9f-9b05-85038ba09db7"
                    button_name = "Добавить"
                elif callback_data.startswith("btn_short_"):
                    url = "https://n8n-tg-marcell88.amvera.io/webhook/83debed4-2cd8-469d-b4dc-d978ec68a785"
                    button_name = "Без комментария"
                elif callback_data.startswith("btn_delete_"):
                    url = "https://n8n-tg-marcell88.amvera.io/webhook/5ccbe3b1-240b-4f47-bb93-d101c0cddee2"
                    button_name = "Удалить"
                else:
                    logger.warning(f"Неизвестный callback: {callback_data}")
                    return web.json_response({"ok": False})
                
                # Получаем текст поста
                post_text = message.get("caption") or message.get("text") or ""
                
                # Отправляем в n8n
                payload = {"id": message_id, "text": post_text}
                logger.info(f"➡️ {button_name}: {message_id}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status in [200, 201, 202, 204]:
                            logger.info(f"✅ {button_name} отправлен")
                        else:
                            logger.error(f"❌ {button_name} ошибка: {resp.status}")
                
                # Отвечаем Telegram
                async with aiohttp.ClientSession() as tg_session:
                    tg_url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
                    await tg_session.post(tg_url, json={
                        "callback_query_id": callback.get("id"),
                        "text": f"✅ {button_name}",
                        "show_alert": False
                    })
            
            return web.json_response({"ok": True})
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return web.json_response({"ok": False})
    
    async def health(self, request):
        return web.json_response({"status": "ok", "service": "editor_reaction"})
    
    async def run_monitoring(self):
        """Запускает HTTP сервер."""
        logger.info(f"🚀 Запуск Editor Reaction хука на порту {self.WEBHOOK_PORT}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.WEBHOOK_PORT)
        await site.start()
        
        logger.info(f"✅ Хук запущен на http://0.0.0.0:{self.WEBHOOK_PORT}/webhook/editor")
        
        while True:
            await asyncio.sleep(3600)