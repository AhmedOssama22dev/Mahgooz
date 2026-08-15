# Mahgouz mobile

Flutter app for padel court booking in Sheikh Zayed. **Book. Pay. Play.**

## Run

```bash
cd mobile
flutter pub get
flutter run
```

The app talks to the Railway API:

`https://server-production-7b2c.up.railway.app/api/v1`

Override for local Django with:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

If the backend is unreachable, the app falls back to bundled mock JSON and stays fully usable.

## Demo accounts

| Role | Credentials |
|------|-------------|
| Customer | `01012345678` / `secret12` |
| Staff PIN | `1234` |
