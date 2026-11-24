# RageStars activation backend

Отдельный сервис RageStars. Существующий сервис AUTHGUARD не изменяется.

## Render
- Runtime: Python
- Root Directory: `ragestars`
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Plan: Free
- Environment variables: `DATABASE_URL` (PostgreSQL internal URL), `ADMIN_SECRET` (случайный длинный секрет), `TOKEN_SECRET` (отдельный случайный длинный секрет).

Можно использовать существующую PostgreSQL только если в ней разрешено создать отдельную таблицу `ragestars_licenses`. Она не затрагивает таблицу `licenses` AUTHGUARD. Текущая бесплатная БД указана Render как истекающая 10 декабря 2026 года; до этого срока надо экспортировать данные или решить вопрос с постоянным хранением. Не переходите на платный тариф без своего решения.

## API
- `POST /activate`: `{"code":"32 HEX CHARS","installation_id":"stable random id >=20 chars"}`
- `POST /check`: `{"license_id":"...","installation_id":"...","token":"..."}`
- `POST /admin/codes`: заголовок `X-Admin-Secret`, JSON `{"plan":"minute|week|month|forever"}`
- `POST /admin/list`, `POST /admin/revoke`: тот же заголовок.

Срок начинается при первой активации. Одноразовый код привязывается к первой установке. Бессрочный код создаётся только из защищённой админ-панели.

## Ограничения
Это сервер лицензий, не готовая модификация APK. В существующий бинарный APK клиентская проверка ещё не интегрирована. Для подключения нужен исходный Android-проект или безопасная точка интеграции; нативная библиотека текущего APK закрыта/strip-нутa. `installation_id` не является аппаратной аттестацией и не предотвращает модификацию клиента.
