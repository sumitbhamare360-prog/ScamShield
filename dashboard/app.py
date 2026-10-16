"""Streamlit dashboard for the ScamShield API."""

from __future__ import annotations

import html
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests
import streamlit as st


API_URL = os.environ.get("SCAMSHIELD_API_URL", "http://localhost:8000").rstrip("/")
SERVICE_ERROR = "ScamShield service is not running. Start it with: uvicorn scamshield.api:app --port 8000"
FAVICON = Path(__file__).parent / "assets" / "favicon.png"

MOCK_VERDICT: dict[str, Any] = {
    "score": 82,
    "category": "High-Risk Scam",
    "confidence": "high",
    "confidence_note": "The models agree and several indicators were found.",
    "scam_type": "Fake KYC or bank alert",
    "uncertain": False,
    "model_agreement": 0.96,
    "highlights": [{"text": "verify", "start": 0, "end": 6, "weight": 0.18}],
    "checks": {
        "transformer": {"name": "transformer", "score": 94, "weight": 0.4, "status": "ok", "evidence": [], "detail": ""},
        "lstm": {"name": "lstm", "score": 90, "weight": 0.15, "status": "ok", "evidence": [], "detail": ""},
        "rules": {"name": "rules", "score": 78, "weight": 0.2, "status": "ok", "evidence": [{"rule_id": "URGENT_ACTION", "reason": "Urgent account action requested", "severity": 0.8}], "detail": ""},
        "links": {"name": "links", "score": 80, "weight": 0.15, "status": "ok", "evidence": [{"rule_id": "REPUTATION_MALICIOUS", "reason": "URLhaus reported malicious link (https://offers.example/claim)", "severity": 1.0}], "detail": ""},
        "sender": {"name": "sender", "score": 45, "weight": 0.1, "status": "ok", "evidence": [], "detail": ""},
    },
    "actions": [
        "Do not use links in the message. Open your bank app or website directly.",
        "Never share your OTP, UPI PIN, or passwords",
        "Report at 1930 or cybercrime.gov.in",
    ],
    "report_text": "High-Risk Scam, score 82. Fake KYC or bank alert. Review the evidence and do not share credentials.",
    "scan_id": 1,
}

MOCK_HISTORY: list[dict[str, Any]] = [
    {
        "id": 1,
        "created_at": "2026-10-16T09:00:00+00:00",
        "channel": "sms",
        "masked_text": "Your bank account needs review. [OTP]",
        "verdict": MOCK_VERDICT,
    }
]


class DashboardServiceError(Exception):
    """Safe message for API failures shown in the dashboard."""


def mock_mode() -> bool:
    return os.environ.get("SCAMSHIELD_MOCK") == "1"


def api_request(method: str, path: str, **kwargs: Any) -> Any:
    """Call the API, or return fixed examples when mock mode is enabled."""
    if mock_mode():
        if path == "/analyze" or path == "/analyze-image":
            return dict(MOCK_VERDICT)
        if path == "/history":
            return list(MOCK_HISTORY)
        if path == "/blocklist":
            if method.upper() == "GET":
                return ["offers.example", "5550100199"]
            return {"status": "ok"}
        if path.startswith("/history/") or path == "/feedback":
            return {"status": "ok"}
        return {"status": "ok"}

    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=45, **kwargs)
    except requests.RequestException as exc:
        if isinstance(exc, requests.ConnectionError) or isinstance(exc, requests.Timeout):
            raise DashboardServiceError(SERVICE_ERROR) from None
        raise DashboardServiceError("The request could not be completed.") from None

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not response.ok:
        if isinstance(payload, dict):
            error = payload.get("error")
            message = payload.get("message")
            parts = [str(value) for value in (error, message) if isinstance(value, str) and value]
            if parts:
                raise DashboardServiceError(": ".join(parts))
        raise DashboardServiceError(f"The service returned an error ({response.status_code}).")
    return payload


def format_highlights(highlights: list[dict[str, Any]]) -> str:
    """Return escaped markup for only the highlight words from the API."""
    safe_words = [
        f"<mark>{html.escape(str(item.get('text', '')))}</mark>"
        for item in highlights
        if isinstance(item, dict) and item.get("text")
    ]
    return " · ".join(safe_words)


def find_evidence_urls(verdict: dict[str, Any]) -> list[str]:
    links = verdict.get("checks", {}).get("links", {})
    found: list[str] = []
    for evidence in links.get("evidence", []):
        reason = evidence.get("reason", "") if isinstance(evidence, dict) else ""
        reason_text = str(reason)
        values = re.findall(r"https?://[^\s)]+", reason_text)
        remaining = re.sub(r"https?://[^\s)]+", " ", reason_text)
        values.extend(
            "https://" + host
            for host in re.findall(r"(?i)(?<![\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?:/[\w./?%#=&+-]*)?", remaining)
        )
        for value in values:
            clean_value = value.rstrip(".,;")
            if clean_value not in found:
                found.append(clean_value)
    return found


def blocklist_payload(value: str, kind: str = "domain") -> dict[str, str]:
    return {"kind": kind, "value": value}


def _show_api_error(error: Exception) -> None:
    st.error(str(error))


def _uncertain_headline(verdict: dict[str, Any]) -> str | None:
    if verdict.get("category") != "Uncertain: verify manually":
        return None
    score = verdict.get("score")
    if isinstance(score, (int, float)) and score >= 55:
        return "Likely scam. The two models disagree, so verify before acting."
    return "Verify manually. The two models disagree."


def _queue_analysis() -> None:
    if st.session_state.get("request_pending", False):
        return
    image_file = st.session_state.get("analysis_image")
    image_data = None
    if image_file is not None:
        image_data = (image_file.name, image_file.getvalue(), image_file.type or "application/octet-stream")
    channel = st.session_state.get("analysis_channel", "unknown")
    st.session_state.pending_analysis = {
        "text": st.session_state.get("analysis_text", ""),
        "channel": channel,
        "sender": st.session_state.get("analysis_sender") if channel == "email" else None,
        "subject": st.session_state.get("analysis_subject") if channel == "email" else None,
        "use_reputation": st.session_state.get("analysis_use_reputation", False),
        "image": image_data,
    }
    st.session_state.request_pending = True


def _render_verdict(verdict: dict[str, Any]) -> None:
    headline = _uncertain_headline(verdict)
    if headline:
        st.subheader(headline)
    st.subheader("Analysis result")
    score_col, category_col, confidence_col = st.columns(3)
    score_col.metric("Risk score", f"{verdict.get('score', 'Unavailable')} / 100")
    category_col.metric("Category", verdict.get("category", "Uncertain: verify manually"))
    confidence_col.metric("Confidence", verdict.get("confidence", "medium"))
    st.caption(verdict.get("confidence_note", "Confidence details are unavailable."))

    highlights = verdict.get("highlights") or []
    if highlights:
        st.markdown("**Highlighted indicators**")
        # Highlight strings are escaped by format_highlights before HTML rendering.
        st.markdown(format_highlights(highlights), unsafe_allow_html=True)
    else:
        st.info("No text highlights are available for this result.")

    model_cols = st.columns(5)
    checks = verdict.get("checks", {})
    for column, name, label in zip(
        model_cols,
        ("transformer", "lstm", "rules", "links", "sender"),
        ("Transformer", "BiLSTM", "Rules", "Links", "Sender"),
    ):
        check = checks.get(name, {})
        score = check.get("score")
        column.metric(label, f"{score:g}" if isinstance(score, (int, float)) else "Unavailable", check.get("status", "not_checked"))
    agreement = verdict.get("model_agreement")
    st.caption(f"Model agreement: {agreement if agreement is not None else 'not available'}")

    with st.expander("Evidence by check"):
        for name, check in checks.items():
            st.markdown(f"**{name.title()} · {check.get('status', 'unknown')}**")
            evidence = check.get("evidence", [])
            if evidence:
                for item in evidence:
                    st.write(f"{item.get('rule_id', 'Indicator')}: {item.get('reason', 'No detail available.')}")
            elif check.get("detail"):
                st.write(check["detail"])
            else:
                st.write("No evidence recorded.")

    st.markdown("**Recommended actions**")
    actions = verdict.get("actions", [])
    if actions:
        st.markdown("\n".join(f"- {action}" for action in actions))
    st.download_button(
        "Download report",
        data=verdict.get("report_text", ""),
        file_name="scamshield-report.txt",
        mime="text/plain",
    )

    scan_id = verdict.get("scan_id")
    if scan_id is not None:
        feedback_col, feedback_col2 = st.columns(2)
        for col, label, feedback in ((feedback_col, "Mark as scam", "scam"), (feedback_col2, "Mark as safe", "safe")):
            key = f"feedback_{scan_id}_{feedback}"
            if col.button(label, key=key):
                try:
                    api_request("POST", "/feedback", json={"scan_id": scan_id, "label": feedback})
                    st.success("Feedback saved.")
                except DashboardServiceError as error:
                    _show_api_error(error)

    for url in find_evidence_urls(verdict):
        if st.button(f"Block link: {url}", key=f"block_evidence_{url}"):
            try:
                # links.py compares URL and domain values; the store uses this API-tested kind.
                api_request("POST", "/blocklist", json=blocklist_payload(url))
                st.success("Link added to the blocklist.")
            except DashboardServiceError as error:
                _show_api_error(error)


def _analyze_page() -> None:
    st.title("Analyze a message")
    with st.form("analyze_form"):
        st.text_area("Message text", height=180, max_chars=5000, key="analysis_text", disabled=st.session_state.get("request_pending", False))
        channel = st.selectbox("Channel", ("sms", "whatsapp", "email", "unknown"), key="analysis_channel", disabled=st.session_state.get("request_pending", False))
        if channel == "email":
            st.text_input("Sender", key="analysis_sender", disabled=st.session_state.get("request_pending", False))
            st.text_input("Subject", key="analysis_subject", disabled=st.session_state.get("request_pending", False))
        st.file_uploader("Or upload a screenshot", type=("png", "jpg", "jpeg", "webp"), key="analysis_image", disabled=st.session_state.get("request_pending", False))
        st.toggle("Check link reputation", value=False, key="analysis_use_reputation", disabled=st.session_state.get("request_pending", False))
        st.form_submit_button("Analyze", disabled=st.session_state.get("request_pending", False), on_click=_queue_analysis)

    if st.session_state.get("request_pending"):
        pending = st.session_state.get("pending_analysis", {})
        try:
            with st.spinner("Analyzing message…"):
                if pending.get("image") is not None:
                    files = {"file": pending["image"]}
                    data = {"channel": pending["channel"], "use_reputation": str(pending["use_reputation"]).lower()}
                    if pending.get("sender"):
                        data["sender"] = pending["sender"]
                    if pending.get("subject"):
                        data["subject"] = pending["subject"]
                    result = api_request("POST", "/analyze-image", files=files, data=data)
                else:
                    result = api_request("POST", "/analyze", json={"text": pending.get("text", ""), "channel": pending["channel"], "sender": pending.get("sender"), "subject": pending.get("subject"), "use_reputation": pending["use_reputation"]})
            st.session_state.latest_verdict = result
            st.session_state.latest_channel = pending["channel"]
        except DashboardServiceError as error:
            _show_api_error(error)
        finally:
            st.session_state.request_pending = False
            st.session_state.pop("pending_analysis", None)
        st.rerun()

    if st.session_state.get("latest_verdict"):
        _render_verdict(st.session_state.latest_verdict)


def _history_page() -> None:
    st.title("Scan history")
    try:
        entries = api_request("GET", "/history")
    except DashboardServiceError as error:
        _show_api_error(error)
        return
    if not entries:
        st.info("No saved scans yet.")
        return

    channel_options = ["All"] + sorted({item.get("channel", "unknown") for item in entries})
    channel_filter = st.selectbox("Channel filter", channel_options)
    category_options = ["All"] + sorted({item.get("verdict", {}).get("category", "Unknown") for item in entries})
    category_filter = st.selectbox("Category filter", category_options)
    scores = [int(item.get("verdict", {}).get("score", 0)) for item in entries]
    score_filter = st.slider("Score range", 0, 100, (min(scores), max(scores)))
    start_date = st.date_input("From date", value=date(2000, 1, 1))
    end_date = st.date_input("Through date", value=date.today())

    visible = []
    for item in entries:
        verdict = item.get("verdict", {})
        try:
            created = datetime.fromisoformat(item.get("created_at", "")).date()
        except ValueError:
            created = date.min
        score = int(verdict.get("score", 0))
        if channel_filter != "All" and item.get("channel") != channel_filter:
            continue
        if category_filter != "All" and verdict.get("category") != category_filter:
            continue
        if not (score_filter[0] <= score <= score_filter[1] and start_date <= created <= end_date):
            continue
        visible.append(item)

    if not visible:
        st.info("No history items match these filters.")
    for item in visible:
        verdict = item.get("verdict", {})
        with st.expander(f"{item.get('created_at', 'Unknown date')} · {item.get('channel', 'unknown')} · {verdict.get('category', 'Unknown')} · {verdict.get('score', 'Unavailable')}/100"):
            st.write(item.get("masked_text", ""))
            st.write(verdict.get("report_text", ""))
            confirm_key = f"confirm_delete_{item['id']}"
            if st.checkbox("Confirm delete this scan", key=confirm_key) and st.button("Delete scan", key=f"delete_{item['id']}"):
                try:
                    api_request("DELETE", f"/history/{item['id']}")
                    st.success("Scan deleted.")
                    st.rerun()
                except DashboardServiceError as error:
                    _show_api_error(error)

    if st.checkbox("Confirm clear all history", key="confirm_clear_history") and st.button("Clear all history", key="clear_history"):
        try:
            api_request("DELETE", "/history")
            st.success("History cleared.")
            st.rerun()
        except DashboardServiceError as error:
            _show_api_error(error)


def _blocklist_page() -> None:
    st.title("Blocklist")
    with st.form("blocklist_form"):
        kind = st.selectbox("Entry type", ("domain", "phone"))
        value = st.text_input("URL, domain, or phone number")
        submitted = st.form_submit_button("Add to blocklist")
    if submitted:
        try:
            api_request("POST", "/blocklist", json=blocklist_payload(value, kind))
            st.success("Entry added to the blocklist.")
        except DashboardServiceError as error:
            _show_api_error(error)
    try:
        values = api_request("GET", "/blocklist")
    except DashboardServiceError as error:
        _show_api_error(error)
        return
    if values:
        for item in values:
            st.write(item)
    else:
        st.info("The blocklist is empty.")


def main() -> None:
    st.set_page_config(page_title="ScamShield", page_icon=str(FAVICON), layout="wide")
    st.html("<style>:root{color-scheme:light;--primary-color:#176b67;--text-color:#1f2933;--background-color:#f5f6f8;--secondary-background-color:#e9edf2}.stApp{background:#f5f6f8;color:#1f2933}section[data-testid='stSidebar']{background:#e9edf2}.stApp p,.stApp h1,.stApp h2,.stApp h3,.stApp label,.stApp span{color:#1f2933}.stTextArea textarea,.stTextInput input,[data-baseweb='select']>div{background:#fff!important;color:#1f2933!important;border-color:#c5ccd3!important}.stButton button,.stDownloadButton button{border-radius:5px;background:#176b67;color:#fff;border-color:#176b67}</style>")
    with st.sidebar:
        st.title("ScamShield")
        page = st.radio("Pages", ("Analyze", "History", "Blocklist"), label_visibility="collapsed")
        if mock_mode():
            st.caption("Demo mode")
        else:
            st.caption(f"Service: {API_URL}")
    if page == "Analyze":
        _analyze_page()
    elif page == "History":
        _history_page()
    else:
        _blocklist_page()


if __name__ == "__main__":
    main()
