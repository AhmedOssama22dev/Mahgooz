# Mahgouz mobile

Flutter app for padel court booking in Sheikh Zayed. **Book. Pay. Play.**

## Run

```bash
cd mobile
flutter pub get
flutter run
```

The app talks to `http://127.0.0.1:8000/api/v1` (Android emulator: `http://10.0.2.2:8000/api/v1`). Override with:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

If the backend is unreachable, the app falls back to bundled mock JSON and stays fully usable.

## Demo accounts

| Role | Credentials |
|------|-------------|
| Customer | `01012345678` / `secret12` |
| Staff PIN | `1234` |
