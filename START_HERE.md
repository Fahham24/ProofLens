# START HERE

## 1. Create environment

Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Configure genuine reverse-image search

Put your SerpApi key in `.env`:

```env
SERPAPI_KEY=your_key
```

The app uses the real Google Lens search endpoint through SerpApi. There are no hardcoded search results.

## 3. Test the local pipeline

```bash
python scripts/test_core.py
```

## 4. Run the UI

```bash
streamlit run frontend/streamlit_app.py
```

## 5. Optional blockchain

Put a burner Polygon Amoy private key in `.env`:

```env
POLYGON_PRIVATE_KEY=0x...
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology/
```

Deploy:

```bash
python scripts/deploy_contract.py
```

Copy the printed address into:

```env
EVIDENCE_CONTRACT_ADDRESS=0x...
```

Restart Streamlit.

## 6. Hackathon demo

Use a photo you have permission to process.

- Upload image
- Show local face detection
- Show SHA-256 and pHash
- Run genuine reverse-image search
- Pick a real returned match
- Download/show evidence JSON
- Anchor evidence hash to Polygon Amoy
- Verify the hash
- Change one evidence field and show verification fails

Never commit `.env` or a private key.
