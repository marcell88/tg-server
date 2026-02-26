# hooks/preview_reaction.py
import aiohttp
import asyncio
import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)

class PreviewReaction:
    """Хук для обработки нажатий кнопок."""
    
    WEBHOOK_PORT = 8081  # Тот же порт что и был
    
    def __init__(self):
        self.bot_token = os.getenv('PUBLISH_API')
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов."""
        self.app.router.add_post('/webhook/telegram', self.telegram_webhook)
        self.app.router.add_get('/health', self.health)
    
    async def telegram_webhook(self, request):
        """Принимает нажатия кнопок от Telegram."""
        try:
            update = await request.json()
            logger.info(f"📩 Получен вебхук")
            
            if "callback_query" in update:
                callback = update["callback_query"]
                callback_data = callback.get("data", "")
                message = callback.get("message", {})
                message_id = message.get("message_id")
                
                post_text = message.get("caption") or message.get("text") or ""
                
                if callback_data.startswith("btn_image_"):
                    url = "https://n8n-tg-marcell88.amvera.io/webhook/35e1e741-9733-48b2-a335-2e3969368460"
                    button_name = "Картинка"
                elif callback_data.startswith("btn_post_"):
                    url = "https://n8n-tg-marcell88.amvera.io/webhook/81fc81a9-3208-462a-a858-bc27c0460fdf"
                    button_name = "Пост"
                else:
                    return web.json_response({"ok": False})
                
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
                        "text": "✅ Отправлено",
                        "show_alert": False
                    })
            
            return web.json_response({"ok": True})
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return web.json_response({"ok": False})
    
    async def health(self, request):
        return web.json_response({"status": "ok", "service": "preview_reaction"})
    
    async def run_monitoring(self):
        """Запускает HTTP сервер."""
        logger.info(f"🚀 Запуск Preview Reaction хука на порту {self.WEBHOOK_PORT}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.WEBHOOK_PORT)
        await site.start()
        
        logger.info(f"✅ Хук запущен на http://0.0.0.0:{self.WEBHOOK_PORT}/webhook/telegram")
        logger.info(f"📡 Nginx проксирует https://server.10pages.tech → http://127.0.0.1:{self.WEBHOOK_PORT}")
        
        while True:
            await asyncio.sleep(3600)