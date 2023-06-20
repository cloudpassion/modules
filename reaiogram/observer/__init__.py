from ..handlers.observer.event.simple import register_simple_event_observer
from ..handlers.observer.telegram_event.simple import register_simple_telegram_event_observer
from ..handlers.observer.telegram_event.logging import register_log_update_telegram_event_observer
from ..handlers.observer.telegram_event.orm import register_save_update_telegram_event_observer


def register_observers(dp):

    register_simple_event_observer(dp)
    register_simple_telegram_event_observer(dp)

    register_log_update_telegram_event_observer(dp)

    register_save_update_telegram_event_observer(dp)


