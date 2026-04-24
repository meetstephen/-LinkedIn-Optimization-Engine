"""
data_manager.py — Data Management page.

Features
--------
  • Export full backup  → downloads a timestamped .json file containing every
                          post in the current user's library plus metadata.
  • Restore from backup → upload a previously exported .json file; choose to
                          MERGE (keep existing posts + add from backup) or
                          REPLACE (wipe existing and import from backup).
  • Quick stats         → shows what is currently stored before any action.
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime

import streamlit as st

# ── Try to import core DB layer ────────────────────────────────────────────────
try:
    from core import db as _db
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False


# ── Backup schema version ──────────────────────────────────────────────────────
BACKUP_VERSION = "1.0"


# ─────────────────────────────────────────────────────────────────────────────
def render_data_manager():

    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Export · Import · Restore</div>
        <h1>🗄️ Data Manager</h1>
        <p>Back up every post you've ever saved — or restore from a previous backup</p>
    </div>
    """, unsafe_allow_html=True)

    if not _CORE_AVAILABLE:
        st.error(
            "⚠️ The `core/` modules are not installed. "
            "Make sure `core/db.py`, `core/ai.py`, and `core/state.py` exist in your repo."
        )
        return

    # ── Current library stats ─────────────────────────────────────────────────
    try:
        stats = _db.get_stats()
    except Exception:
        st.error("⚠️ Could not read the database. Please try again.")
        with st.expander("🔍 Details"):
            st.code(traceback.format_exc())
        return

    st.markdown("### 📊 Current Library")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📝 Total Posts", stats["total"])
    with c2:
        st.metric("⭐ Starred", stats["starred"])
    with c3:
        st.metric("📊 Avg Hook Score", f"{stats['avg_score']}/100" if stats["avg_score"] else "N/A")
    with c4:
        st.metric("🏆 Most Used Module", stats["top_module"])

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXPORT
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### 📤 Export Full Backup")
    st.caption(
        "Downloads every post in your library as a single JSON file. "
        "Keep this file somewhere safe — you can use it to restore later."
    )

    if stats["total"] == 0:
        st.info("📭 Your library is empty — nothing to export yet.")
    else:
        export_col, preview_col = st.columns([1, 1], gap="large")

        with export_col:
            if st.button("⬇️ Generate Backup File", type="primary", key="export_btn"):
                with st.spinner("Building backup…"):
                    try:
                        all_posts = _db.get_posts()
                        backup = {
                            "backup_version": BACKUP_VERSION,
                            "exported_at":    datetime.now().isoformat(),
                            "total_posts":    len(all_posts),
                            "posts":          all_posts,
                        }
                        st.session_state["_export_json"] = json.dumps(backup, indent=2)
                        st.session_state["_export_filename"] = (
                            f"linkedin_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        )
                        st.success(f"✅ Backup ready — {len(all_posts)} posts packaged.")
                    except Exception:
                        st.error("⚠️ Something went wrong while building the backup.")
                        with st.expander("🔍 Details"):
                            st.code(traceback.format_exc())

            # Show download button once the backup is ready
            if st.session_state.get("_export_json"):
                st.download_button(
                    label="💾 Download Backup (.json)",
                    data=st.session_state["_export_json"],
                    file_name=st.session_state.get("_export_filename", "linkedin_backup.json"),
                    mime="application/json",
                    use_container_width=True,
                    key="export_download_btn",
                )

        with preview_col:
            if st.session_state.get("_export_json"):
                try:
                    preview_data = json.loads(st.session_state["_export_json"])
                    st.markdown(f"""
                    <div style="background:#F8FBFF; border:1.5px solid #C7D9F5;
                                border-radius:12px; padding:1.2rem;">
                        <div style="font-weight:700; color:#0A66C2; margin-bottom:0.6rem;">
                            📦 Backup Summary
                        </div>
                        <div style="font-size:0.88rem; color:#333; line-height:1.8;">
                            <b>Version:</b> {preview_data['backup_version']}<br>
                            <b>Exported:</b> {preview_data['exported_at'][:19].replace('T', ' ')}<br>
                            <b>Posts:</b> {preview_data['total_posts']}<br>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    pass

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — RESTORE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### 📥 Restore from Backup")
    st.caption("Upload a `.json` backup file exported from this app.")

    uploaded = st.file_uploader(
        "Choose a backup file",
        type=["json"],
        key="restore_upload",
        label_visibility="collapsed",
    )

    if uploaded:
        # ── Parse and validate ────────────────────────────────────────────────
        try:
            raw = json.loads(uploaded.read())
        except json.JSONDecodeError:
            st.error("⚠️ That file doesn't look like valid JSON. Please upload a backup exported from this app.")
            return

        # Accept both versioned backups and raw post arrays
        if isinstance(raw, list):
            posts = raw
            exported_at = "unknown"
        elif isinstance(raw, dict) and "posts" in raw:
            posts = raw["posts"]
            exported_at = raw.get("exported_at", "unknown")[:19].replace("T", " ")
        else:
            st.error("⚠️ Unrecognised backup format. Please upload a file exported from this app.")
            return

        # Validate each post has the minimum required fields
        valid_posts = [
            p for p in posts
            if isinstance(p, dict) and "content" in p and "module" in p
        ]
        skipped = len(posts) - len(valid_posts)

        # ── Preview ───────────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#F0FFF4; border:1.5px solid #A8E6C3;
                    border-radius:12px; padding:1.2rem; margin-bottom:1rem;">
            <div style="font-weight:700; color:#067934; margin-bottom:0.5rem;">
                ✅ Backup file looks good
            </div>
            <div style="font-size:0.88rem; color:#333; line-height:1.8;">
                <b>Posts found:</b> {len(valid_posts)}<br>
                {"<b>Skipped (invalid):</b> " + str(skipped) + "<br>" if skipped else ""}
                {"<b>Originally exported:</b> " + exported_at + "<br>" if exported_at != "unknown" else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Restore mode ──────────────────────────────────────────────────────
        st.markdown("**Choose restore mode:**")
        mode = st.radio(
            "Restore mode",
            [
                "🔀 Merge — add backup posts to my existing library",
                "♻️ Replace — wipe my library and import only from backup",
            ],
            key="restore_mode",
            label_visibility="collapsed",
        )

        if "Replace" in mode:
            st.warning(
                "⚠️ **Replace mode** will permanently delete all your current posts "
                "before importing. This cannot be undone. Make sure you have a backup first."
            )

        # ── Confirm and execute ───────────────────────────────────────────────
        confirm = st.checkbox(
            "I understand and want to proceed with the restore",
            key="restore_confirm",
        )

        if confirm:
            if st.button("🔄 Restore Now", type="primary", key="restore_btn"):
                with st.spinner("Restoring…"):
                    try:
                        engine = _db._get_engine()
                        from sqlalchemy import text as _text

                        if "Replace" in mode:
                            # Delete all current user's posts first
                            uid = _db._user_id()
                            with engine.begin() as conn:
                                conn.execute(
                                    _text("DELETE FROM posts WHERE user_id = :uid"),
                                    {"uid": uid},
                                )

                        # Import each valid post
                        imported = 0
                        for p in valid_posts:
                            try:
                                _db.save_post(
                                    content=p["content"],
                                    module=p.get("module", "Imported"),
                                    score=p.get("score", 0),
                                    tags=p.get("tags", []),
                                )
                                imported += 1
                            except Exception:
                                pass  # skip individual bad rows silently

                        # Reset session counter to match new DB state
                        new_stats = _db.get_stats()
                        st.session_state["session_posts_generated"] = new_stats["total"]

                        st.success(
                            f"✅ Restore complete! "
                            f"**{imported}** post{'s' if imported != 1 else ''} imported. "
                            f"Head to **📚 Post Library** to see them."
                        )

                    except Exception:
                        st.error("⚠️ Something went wrong during restore.")
                        with st.expander("🔍 Details"):
                            st.code(traceback.format_exc())

    st.markdown("---")
    st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit · Gemini AI · Stability AI · Hugging Face<br>
        <em>Not affiliated with LinkedIn. No scraping. All content is AI-generated.</em>
    </div>
    """, unsafe_allow_html=True)
