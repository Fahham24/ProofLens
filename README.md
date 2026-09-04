# ProofLens

Privacy-preserving image provenance verification for a hackathon.

## What it does

1. Accepts a user-provided image.
2. Detects faces locally with OpenCV.
3. Creates a non-identifying visual face signature plus SHA-256 and perceptual image hashes.
4. Performs a genuine reverse-image search with Google Lens through SerpApi when `SERPAPI_KEY` is configured.
5. Downloads candidate public images and compares them with perceptual hashing.
6. Builds an evidence JSON document.
7. Hashes the evidence document with SHA-256.
8. Optionally anchors that evidence hash on Polygon Amoy.
9. Verifies the local evidence hash against the on-chain record.

This project does **not** identify a person, infer identity, or search for a person's social-media account from their face.

## Architecture

```text
Upload
  |
  +--> Face detection (OpenCV)
  |
  +--> Image SHA-256 + pHash
  |
  +--> Local visual face signature
  |
  +--> Google Lens via SerpApi
          |
          +--> visual matches
          |
          +--> candidate URLs
                    |
                    +--> pHash comparison
  |
  +--> Evidence JSON
  |
  +--> SHA-256 evidence hash
  |
  +--> Polygon Amoy (optional)
```

## Requirements

- Python 3.10+
- Internet connection for reverse-image search and blockchain
- SerpApi account/API key for genuine Google Lens search
- A Polygon Amoy burner wallet with test POL if you want blockchain writes

SerpApi's current Google Lens API supports direct local image uploads through its Image API. Uploaded images can be JPG/JPEG, PNG, or WebP and are limited to 500 KB; the temporary image ID expires after 10 minutes.

Polygon Amoy is testnet chain ID `80002`.

## Setup

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
SERPAPI_KEY=your_serpapi_key

POLYGON_RPC_URL=https://rpc-amoy.polygon.technology/
POLYGON_PRIVATE_KEY=
EVIDENCE_CONTRACT_ADDRESS=
```

Keep the private key out of GitHub. Use a burner/test wallet only.

## Run the app

```bash
streamlit run frontend/streamlit_app.py
```

Then open the local URL shown by Streamlit.

## Deploy the smart contract

Install the requirements first.

Set:

```env
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology/
POLYGON_PRIVATE_KEY=0xyour_burner_private_key
```

Run:

```bash
python scripts/deploy_contract.py
```

Copy the printed contract address into `.env`:

```env
EVIDENCE_CONTRACT_ADDRESS=0x...
```

Restart Streamlit.

## Demo flow

1. Use a photo of a consenting participant or a non-sensitive test image.
2. Upload it.
3. Show face detection and fingerprints.
4. Click **Run genuine reverse-image search**.
5. Select a returned public visual match.
6. Show the candidate URL, source, exact-match flag, and pHash similarity.
7. Create the evidence record.
8. Click **Anchor on Polygon Amoy**.
9. Show the transaction hash.
10. Change one evidence field locally and run verification. The local hash will no longer match the anchored hash.

## Important limitation

A reverse-image match proves that an image or visually similar image was found at a public URL. It does not prove who owns the account, who originally created the image, or the identity of a person in the image.

The blockchain proves integrity of the evidence hash after anchoring. It does not make the underlying search result truthful.

## Suggested hackathon pitch

> ProofLens creates tamper-evident evidence for public image provenance without putting biometric data on-chain. It detects a face locally, fingerprints the image, performs a genuine reverse-image search, scores returned visual matches, creates an evidence package, and anchors only the evidence hash to Polygon Amoy.

## License

MIT for the original project code. Review third-party service/model licenses before deployment.
