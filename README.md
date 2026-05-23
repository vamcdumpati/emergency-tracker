# 🚨 Emergency Location Tracker – Backend

A **100% free** FastAPI backend for a Flutter emergency location-sharing app.

---

## 🗂 Project Structure

```
emergency-tracker/
├── main.py                        # FastAPI entry point
├── requirements.txt
├── render.yaml                    # One-click Render.com deploy
├── .env.example                   # Copy to .env and fill in
├── static/track/map.html          # Live tracking map (Leaflet.js)
└── app/
    ├── db/client.py               # Supabase client + bootstrap SQL
    ├── models/schemas.py          # Pydantic request/response models
    ├── services/
    │   ├── sms.py                 # Fast2SMS integration
    │   └── ws_manager.py         # WebSocket broadcast manager
    └── routers/
        ├── auth.py               # Register / Login
        ├── contacts.py           # Emergency contacts CRUD
        └── tracking.py           # SOS, location stream, map page
```

---

## 🚀 Setup in 4 Steps

### Step 1 – Supabase (Free Database)

1. Go to [supabase.com](https://supabase.com) → New project (free)
2. Open **SQL Editor** and run the SQL from `app/db/client.py` (the `BOOTSTRAP_SQL` string)
3. Copy your **Project URL** and **anon/service key** from Settings → API

### Step 2 – Fast2SMS (Free Indian SMS)

1. Sign up at [fast2sms.com](https://fast2sms.com)
2. Go to **Dashboard → Dev API**
3. Copy your API key

### Step 3 – Local Development

```bash
# Clone and install
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_KEY, FAST2SMS_API_KEY

# Run locally
python main.py
# API docs: http://localhost:8000/docs
```

### Step 4 – Deploy to Render.com (Free Hosting)

1. Push this folder to a **GitHub repo**
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. In Environment Variables, add:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `FAST2SMS_API_KEY`
   - `BASE_URL` → your Render URL (e.g. `https://emergency-tracker.onrender.com`)
5. Deploy! ✅

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login |
| `GET`  | `/auth/user/{id}` | Get user profile |
| `POST` | `/contacts/{user_id}` | Add emergency contact |
| `GET`  | `/contacts/{user_id}` | List emergency contacts |
| `DELETE` | `/contacts/{contact_id}` | Delete contact |
| `POST` | `/sos` | 🚨 Trigger SOS alert + send SMS |
| `POST` | `/sos/{session_id}/stop` | Mark user as safe |
| `WS`   | `/ws/location/{session_id}` | Flutter streams GPS here |
| `WS`   | `/ws/view/{session_id}` | Browser connects for live updates |
| `GET`  | `/track/{token}` | Public tracking map page |

Full interactive docs at `/docs` (Swagger UI).

---

## 📱 Flutter Integration

### 1. Register User
```dart
final res = await http.post(
  Uri.parse('$baseUrl/auth/register'),
  body: jsonEncode({
    'name': 'Rahul',
    'email': 'rahul@email.com',
    'phone': '9876543210',
    'password': 'secret123',
  }),
);
```

### 2. Add Emergency Contact
```dart
await http.post(
  Uri.parse('$baseUrl/contacts/$userId'),
  body: jsonEncode({'name': 'Mom', 'phone': '9123456789'}),
);
```

### 3. Trigger SOS (get current GPS first)
```dart
Position pos = await Geolocator.getCurrentPosition();

final res = await http.post(
  Uri.parse('$baseUrl/sos'),
  body: jsonEncode({
    'user_id': userId,
    'initial_location': {
      'latitude': pos.latitude,
      'longitude': pos.longitude,
      'accuracy': pos.accuracy,
    },
  }),
);

final sessionId = jsonDecode(res.body)['session_id'];
// Now open WebSocket to stream live location:
```

### 4. Stream Live GPS via WebSocket
```dart
import 'package:web_socket_channel/web_socket_channel.dart';

final channel = WebSocketChannel.connect(
  Uri.parse('wss://your-app.onrender.com/ws/location/$sessionId'),
);

// Stream location every 3 seconds
Geolocator.getPositionStream(
  locationSettings: LocationSettings(accuracy: LocationAccuracy.high),
).listen((pos) {
  channel.sink.add(jsonEncode({
    'latitude': pos.latitude,
    'longitude': pos.longitude,
    'accuracy': pos.accuracy,
  }));
});
```

### 5. Stop SOS (user is safe)
```dart
await http.post(Uri.parse('$baseUrl/sos/$sessionId/stop'));
channel.sink.close();
```

---

## 🔒 Security Notes (for production)

- Replace SHA-256 password hashing with **bcrypt** (`passlib[bcrypt]`)
- Add **JWT tokens** for authentication (use `python-jose`)
- Restrict CORS origins to your Flutter app's domain
- Add **rate limiting** to `/sos` endpoint to prevent abuse

---

## 💰 Cost: ₹0/month

| Service | Plan | Cost |
|---------|------|------|
| Render.com | Free web service | ₹0 |
| Supabase | Free tier (500 MB) | ₹0 |
| Fast2SMS | Free credits (~50 SMS) | ₹0 |
| OpenStreetMap / Leaflet | Open source map | ₹0 |
