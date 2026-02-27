# app.py
import asyncio
import logging
import signal
from typing import Dict, Any

# Импортируем все хуки
from hooks.preview_reaction import PreviewReaction
from hooks.editor_reaction import EditorReaction

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === НАСТРОЙКА ХУКОВ ===
ENABLE_PREVIEW_REACTION = True   # Хук для preview бота
ENABLE_EDITOR_REACTION = True    # Хук для editor бота
# ========================

class ServiceManager:
    """Менеджер для управления хуками."""
    
    def __init__(self):
        self.tasks = []
        self.is_running = True
        
        # Инициализируем хуки
        self.services: Dict[str, Any] = {}
        
        if ENABLE_PREVIEW_REACTION:
            self.services["preview_reaction"] = PreviewReaction()
        
        if ENABLE_EDITOR_REACTION:
            self.services["editor_reaction"] = EditorReaction()
        
        # Обработка сигналов остановки
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов остановки."""
        logging.info(f"Получен сигнал остановки {signum}")
        self.is_running = False

    async def initialize_services(self):
        """Инициализация перед запуском."""
        return True

    async def start_background_services(self):
        """Запускает все хуки."""
        services_tasks = []
        
        if ENABLE_PREVIEW_REACTION and "preview_reaction" in self.services:
            services_tasks.append(("Preview-Reaction", self._run_preview_reaction))
        
        if ENABLE_EDITOR_REACTION and "editor_reaction" in self.services:
            services_tasks.append(("Editor-Reaction", self._run_editor_reaction))
        
        if not services_tasks:
            logging.warning("⚠️ Нет активных хуков.")
            return False
        
        logging.info("🎯 Запуск хуков...")
        for name, service_task in services_tasks:
            task = asyncio.create_task(service_task(name))
            self.tasks.append(task)
            await asyncio.sleep(0.5)
        
        return True

    async def _run_preview_reaction(self, name: str):
        """Запускает Preview Reaction хук."""
        try:
            logging.info(f"🚀 Запуск {name}...")
            await self.services["preview_reaction"].run_monitoring()
        except asyncio.CancelledError:
            logging.info(f"{name} остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка в {name}: {e}")

    async def _run_editor_reaction(self, name: str):
        """Запускает Editor Reaction хук."""
        try:
            logging.info(f"🚀 Запуск {name}...")
            await self.services["editor_reaction"].run_monitoring()
        except asyncio.CancelledError:
            logging.info(f"{name} остановлен")
        except Exception as e:
            logging.error(f"❌ Ошибка в {name}: {e}")

    async def stop_services(self):
        """Останавливает все хуки."""
        logging.info("🛑 Остановка...")
        
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            try:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            except Exception as e:
                logging.debug(f"Ошибка при остановке: {e}")

    async def run(self):
        """Основной цикл работы."""
        try:
            if not await self.initialize_services():
                logging.critical("❌ Ошибка инициализации")
                return
            
            logging.info("📋 Статус хуков:")
            logging.info(f"    Preview Reaction: {'✅ ВКЛЮЧЕН' if ENABLE_PREVIEW_REACTION else '❌ ВЫКЛЮЧЕН'}")
            logging.info(f"    Editor Reaction: {'✅ ВКЛЮЧЕН' if ENABLE_EDITOR_REACTION else '❌ ВЫКЛЮЧЕН'}")
            
            has_services = await self.start_background_services()
            
            if has_services:
                logging.info("🏃 Хуки работают...")
                while self.is_running:
                    await asyncio.sleep(1)
            else:
                logging.info("⏳ Нет активных хуков")
                await asyncio.sleep(5)
                self.is_running = False
                
        except KeyboardInterrupt:
            logging.info("Получен KeyboardInterrupt")
        except Exception as e:
            logging.critical(f"Ошибка: {e}")
        finally:
            await self.stop_services()

async def main_services():
    manager = ServiceManager()
    await manager.run()

def start_application():
    logging.info("🚀 Запуск Reaction Hooks...")
    logging.info("=" * 60)
    logging.info("📋 Настройки:")
    logging.info(f"    Preview Reaction: {'✅ ВКЛЮЧЕН' if ENABLE_PREVIEW_REACTION else '❌ ВЫКЛЮЧЕН'}")
    logging.info(f"    Editor Reaction: {'✅ ВКЛЮЧЕН' if ENABLE_EDITOR_REACTION else '❌ ВЫКЛЮЧЕН'}")
    logging.info("=" * 60)
    
    try:
        asyncio.run(main_services())
    except KeyboardInterrupt:
        logging.info("Остановлено пользователем")
    except Exception as e:
        logging.critical(f"Ошибка: {e}")
    finally:
        logging.info("Завершено")

if __name__ == '__main__':
    start_application()