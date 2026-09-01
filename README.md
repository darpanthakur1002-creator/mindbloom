# MindBloom

MindBloom is a cognitive-wellness and memory-care companion for older adults, family members, and caregivers.

## Current slice

- Expo + React Native + TypeScript mobile shell
- Forest green / sage / lavender design tokens from the Stitch export
- Login entry screen using the entered email as the account identity for development
- Home, Games, Garden, Memories, and Family tabs
- FastAPI backend with persisted SQLite data for check-ins, activity progress, memories, invites, and dashboard data
- Mobile API service layer with LAN configuration for a physical Expo Go device

The original Stitch HTML/PNG export is preserved in `docs/stitch-export/` as the visual reference.

## Run the mobile app

```bash
cd mobile
npm install
npx expo start
```

For a physical Android/iOS phone, use the LAN launcher so Expo advertises the computer's Wi-Fi address instead of `127.0.0.1`:

```powershell
cd mobile
npm start
```

If the phone and computer are on different networks, try `npm run start:tunnel` instead.

The main save and progress actions now use the FastAPI backend. The Memory Capsule includes an AI companion chat at `/api/assistant`; set `AI_API_KEY` in `backend/.env` to enable OpenAI replies. Without a key, the backend uses safe local responses for development.

## Run the backend

```bash
cd backend
python -m venv .venv
\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For a physical phone on the same Wi-Fi network, run the backend on the LAN:

```powershell
cd backend
.\start-lan.ps1
```

Then, in a second terminal, run `npm start` from `mobile`. The launcher automatically points the mobile app at the computer's LAN API address.
