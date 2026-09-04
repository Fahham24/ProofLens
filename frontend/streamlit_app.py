from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.blockchain import anchor_evidence, verify_on_chain
from app.config import settings
from app.evidence import build_evidence, canonical_json, evidence_hash
from app.face import annotate_faces, detect_faces, face_signature
from app.fingerprint import perceptual_hash, sha256_bytes
from app.reverse_search import SerpApiLensProvider, score_candidates


st.set_page_config(
    page_title="ProofLens",
    page_icon="🔎",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {font-size: 42px; font-weight: 800; margin-bottom: 0;}
    .subtitle {font-size: 18px; opacity: .75; margin-bottom: 25px;}
    .card {padding: 18px; border: 1px solid rgba(128,128,128,.25);
           border-radius: 14px; margin-bottom: 15px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🔎 ProofLens</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Tamper-evident public image provenance verification</div>',
    unsafe_allow_html=True,
)

st.info(
    "Privacy boundary: this demo detects and encodes a face but does not identify a person "
    "or search for a person's account from their face. Use images you have permission to process."
)

uploaded = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp"],
    help="For reverse-image search, keep the file at or below 500 KB.",
)

if uploaded:
    image_bytes = uploaded.getvalue()

    col1, col2 = st.columns(2)
    with col1:
        st.image(image_bytes, caption=uploaded.name, use_container_width=True)

    with st.spinner("Running local face detection..."):
        face_result = detect_faces(image_bytes)

    with col2:
        annotated = annotate_faces(face_result["image"], face_result["faces"])
        st.image(
            annotated,
            caption=f"{face_result['face_count']} face(s) detected",
            use_container_width=True,
        )

    image_sha = sha256_bytes(image_bytes)
    image_phash = perceptual_hash(image_bytes)

    st.subheader("1. Local analysis")
    a, b, c = st.columns(3)
    a.metric("Faces", face_result["face_count"])
    b.metric("Image SHA-256", image_sha[:16] + "...")
    c.metric("Image pHash", image_phash)

    face_sig = None
    if face_result["face_count"] > 0:
        face_sig = face_signature(
            face_result["image"],
            face_result["faces"][0],
        )
        st.success(
            f"Face encoding created locally: {face_sig['dimensions']} dimensions. "
            "This project uses a non-identifying visual signature, not an identity embedding."
        )
        with st.expander("Encoding details"):
            st.json(face_sig)

    st.subheader("2. Genuine reverse-image search")

    if "search_results" not in st.session_state:
        st.session_state.search_results = None

    if st.button(
        "Run genuine reverse-image search",
        type="primary",
        disabled=not bool(settings.serpapi_key),
    ):
        if len(image_bytes) > 500 * 1024:
            st.error(
                "This image is over 500 KB. Resize/compress it before sending it to the "
                "reverse-image-search provider."
            )
        else:
            try:
                provider = SerpApiLensProvider(settings.serpapi_key)
                with st.spinner("Uploading to Google Lens and retrieving visual matches..."):
                    raw = provider.search(image_bytes, uploaded.name)
                    results = score_candidates(image_bytes, raw)
                st.session_state.search_results = results
            except Exception as exc:
                st.error(f"Reverse-image search failed: {exc}")

    if not settings.serpapi_key:
        st.warning(
            "SERPAPI_KEY is not configured. Add it to .env to enable the real reverse-image search."
        )

    results = st.session_state.search_results

    selected_match = None
    if results:
        st.write(f"Returned {len(results)} visual matches.")
        rows = []
        for idx, item in enumerate(results):
            rows.append(
                {
                    "id": idx,
                    "title": item.title,
                    "source": item.source,
                    "similarity": (
                        f"{item.similarity:.1%}"
                        if item.similarity is not None
                        else "n/a"
                    ),
                    "exact_match": "YES" if item.exact_match else "NO",
                    "social_domain": "YES" if item.social else "NO",
                    "url": item.url,
                }
            )

        st.dataframe(
            rows,
            column_config={
                "url": st.column_config.LinkColumn("Public URL"),
            },
            hide_index=True,
            use_container_width=True,
        )

        eligible = [
            (i, r)
            for i, r in enumerate(results)
            if r.similarity is not None
        ]

        if eligible:
            labels = [
                f"{i}: {r.title[:65]} | similarity={r.similarity:.1%}"
                for i, r in eligible
            ]
            chosen = st.selectbox("Choose the match to anchor", labels)
            selected_index = eligible[labels.index(chosen)][0]
            item = results[selected_index]
            selected_match = {
                "title": item.title,
                "source": item.source,
                "url": item.url,
                "image_url": item.image_url,
                "exact_match": item.exact_match,
                "similarity": item.similarity,
                "social_domain": item.social,
            }

            if item.image_url:
                try:
                    st.image(
                        item.image_url,
                        caption="Candidate image returned by the search provider",
                        width=350,
                    )
                except Exception:
                    pass

            if item.social:
                st.success(
                    "The selected public URL is on a recognized social-platform domain. "
                    "This verifies the URL/domain and image match, not account ownership or identity."
                )

    st.subheader("3. Evidence package")

    evidence = build_evidence(
        filename=uploaded.name,
        image_sha256=image_sha,
        image_phash=image_phash,
        face_result=face_result,
        face_signature_result=face_sig,
        match=selected_match,
    )
    ev_hash = evidence_hash(evidence)

    st.code(ev_hash, language="text")
    st.caption("SHA-256 hash of the canonical evidence JSON.")

    with st.expander("View canonical evidence JSON"):
        st.json(evidence)

    st.download_button(
        "Download evidence JSON",
        data=canonical_json(evidence),
        file_name="prooflens-evidence.json",
        mime="application/json",
    )

    st.subheader("4. Blockchain anchoring")

    if not settings.evidence_contract_address:
        st.warning(
            "Blockchain contract is not configured yet. Deploy EvidenceRegistry.sol and put "
            "its address in EVIDENCE_CONTRACT_ADDRESS."
        )
    else:
        st.write(f"Contract: `{settings.evidence_contract_address}`")
        st.write("Network: Polygon Amoy (chain ID 80002)")

        if st.button(
            "Anchor evidence hash on Polygon Amoy",
            disabled=not bool(settings.polygon_private_key),
        ):
            try:
                with st.spinner("Sending transaction..."):
                    result = anchor_evidence(
                        rpc_url=settings.polygon_rpc_url,
                        private_key=settings.polygon_private_key,
                        contract_address=settings.evidence_contract_address,
                        evidence_hash_hex=ev_hash,
                    )
                st.session_state.last_tx = result
                st.success("Evidence anchored.")
            except Exception as exc:
                st.error(f"Blockchain transaction failed: {exc}")

        if not settings.polygon_private_key:
            st.warning(
                "POLYGON_PRIVATE_KEY is not configured. Use a burner wallet with test POL."
            )

        if "last_tx" in st.session_state:
            tx = st.session_state.last_tx
            st.write(f"Transaction: `{tx['tx_hash']}`")
            st.write(f"Block: `{tx['block_number']}`")
            st.write(f"Submitter: `{tx['submitter']}`")

    st.subheader("5. Tamper check")

    st.write(
        "After anchoring, change any evidence field and recompute its SHA-256. "
        "The modified hash should no longer equal the on-chain hash."
    )

    record_id = st.number_input(
        "On-chain record ID",
        min_value=0,
        value=0,
        step=1,
    )

    if settings.evidence_contract_address and st.button("Verify against blockchain"):
        try:
            result = verify_on_chain(
                rpc_url=settings.polygon_rpc_url,
                contract_address=settings.evidence_contract_address,
                record_id=int(record_id),
                expected_hash_hex=ev_hash,
            )
            if result["valid"]:
                st.success("VALID: local evidence hash matches the anchored hash.")
            else:
                st.error("TAMPER DETECTED: local evidence hash differs from the anchored hash.")
            st.json(result)
        except Exception as exc:
            st.error(f"Verification failed: {exc}")
