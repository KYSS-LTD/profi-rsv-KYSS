# Telegram Mini App notes

Frontend вызывает `Telegram.WebApp.ready()` и `Telegram.WebApp.expand()` при старте.

Для авторизации frontend не проверяет `initData` самостоятельно. Он только отправляет строку `initData` на backend в заголовке `X-Telegram-Init-Data`. Проверка hash должна быть на сервере.

Основные production требования:

- HTTPS обязателен для Mini App URL.
- Домен должен быть указан в BotFather.
- Backend должен сверять hash из initData.
- Нельзя хранить bot token во frontend.
