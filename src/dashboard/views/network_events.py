"""
Local-only Network Events viewer (PostgreSQL).

Requires server-side BLUESENTRA_VIEWER_MSP_ID. Not for multi-user or production deployment.
Launch: streamlit run src/dashboard/app.py --server.address=127.0.0.1
"""

from __future__ import annotations

import html
import uuid
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import get_settings
from backend.app.database.session import get_session_factory
from backend.app.services.network_events_view import (
    DataFreshness,
    EventDetail,
    EventViewFilters,
    TenantScope,
    ViewerConfigError,
    default_time_window,
    format_relative_utc_age,
    get_data_freshness,
    get_event_detail,
    get_event_time_bounds,
    list_customers,
    list_sensors,
    list_sites,
    msp_event_count,
    query_events_page,
    require_viewer_msp_id,
    summarize_events,
)
from src.dashboard.theme import (
    BYTE_UNITS_NOTE,
    ICON_DOWN,
    ICON_GLOBE,
    ICON_LINK,
    ICON_UP,
    format_bytes,
    format_utc_display,
    render_context_bar,
    render_data_freshness_panel,
    render_metric_card,
    render_page_intro,
)

ALL_CUSTOMERS = "All available customers"
ALL_SITES = "All available sites"
ALL_SENSORS = "All available sensors"


def _fmt_port(port: int | None) -> str:
    return "—" if port is None else str(port)


def _fmt_duration(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def _fmt_int(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _row_label(r: Any) -> str:
    ts = r.event_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return f"{ts} UTC · {r.src_ip}:{_fmt_port(r.src_port)} → {r.dst_ip}:{_fmt_port(r.dst_port)}"


def _detail_field(label: str, value: str, *, mono: bool = False) -> None:
    cls = "bs-detail-v mono" if mono else "bs-detail-v"
    st.markdown(
        f'<div class="bs-detail-item"><p class="bs-detail-k">{html.escape(label)}</p>'
        f'<p class="{cls}">{html.escape(value)}</p></div>',
        unsafe_allow_html=True,
    )


def _render_connection_detail(detail: EventDetail) -> None:
    st.markdown('<p class="bs-section-label">Connection</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        _detail_field("Source IP", detail.src_ip, mono=True)
        _detail_field("Source port", _fmt_port(detail.src_port))
    with c2:
        _detail_field("Destination IP", detail.dst_ip, mono=True)
        _detail_field("Destination port", _fmt_port(detail.dst_port))
    with c3:
        _detail_field("Protocol", detail.transport_protocol.upper())
        _detail_field("Service", detail.service if detail.service else "—")
    _detail_field("Source event ID", detail.source_event_id, mono=True)

    st.markdown('<p class="bs-section-label">Traffic</p>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    with t1:
        _detail_field("Originator bytes", format_bytes(detail.orig_bytes))
        _detail_field("Originator packets", _fmt_int(detail.orig_pkts))
    with t2:
        _detail_field("Responder bytes", format_bytes(detail.resp_bytes))
        _detail_field("Responder packets", _fmt_int(detail.resp_pkts))
    with t3:
        _detail_field("Duration (seconds)", _fmt_duration(detail.duration))
    st.caption(
        "Originator and responder describe connection roles in Zeek conn.log. They do not "
        "necessarily map to internal/external or outbound/inbound. A single connection record "
        "does not establish malicious activity."
    )

    st.markdown('<p class="bs-section-label">Context</p>', unsafe_allow_html=True)
    x1, x2, x3 = st.columns(3)
    with x1:
        _detail_field(
            "Event time (UTC)",
            detail.event_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        )
        _detail_field(
            "Ingestion time (UTC)",
            detail.ingested_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        )
    with x2:
        _detail_field("Customer", detail.customer_name)
        _detail_field("Site", detail.site_name)
    with x3:
        _detail_field("Sensor", detail.sensor_name)
        _detail_field("Source type", detail.source_type)
    if detail.linked_device_label:
        _detail_field("Linked device", detail.linked_device_label)

    with st.expander("Original source evidence", expanded=False):
        st.caption("Read-only Zeek JSON as stored during import.")
        st.json(detail.source_record)


def _load_view_data(
    *,
    msp_id: uuid.UUID,
    filters: EventViewFilters,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    db = get_session_factory()()
    try:
        result = query_events_page(
            db,
            msp_id=msp_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )
        summary = summarize_events(db, msp_id=msp_id, filters=filters)
        return {
            "rows": result.rows,
            "total": result.total_matching,
            "summary": summary,
        }
    finally:
        db.close()


def _load_event_detail(
    *,
    msp_id: uuid.UUID,
    event_id: uuid.UUID,
    filters: EventViewFilters,
) -> EventDetail | None:
    db = get_session_factory()()
    try:
        return get_event_detail(
            db, msp_id=msp_id, event_id=event_id, filters=filters
        )
    finally:
        db.close()


def _load_freshness(*, msp_id: uuid.UUID, scope: TenantScope) -> DataFreshness:
    db = get_session_factory()()
    try:
        return get_data_freshness(db, msp_id=msp_id, scope=scope)
    finally:
        db.close()


def _scope_label(customer: str, site: str, sensor: str) -> str:
    return f"{customer} · {site} · {sensor}"


def _freshness_displays(freshness: DataFreshness) -> tuple[str, str, str, str]:
    if freshness.stored_event_count == 0:
        guidance = "Import Zeek conn.log JSONL for this MSP, then refresh."
        return (
            "No imported events",
            guidance,
            "No imported events",
            guidance,
        )
    event_age = format_relative_utc_age(freshness.latest_event_at)
    ingest_age = format_relative_utc_age(freshness.latest_ingested_at)
    return (
        format_utc_display(freshness.latest_event_at),
        f"When the network activity occurred ({event_age}).",
        format_utc_display(freshness.latest_ingested_at),
        "When the newest stored row was written ({0}). Importing an old log today "
        "does not make its activity current.".format(ingest_age),
    )


def _table_filter_excludes_latest(
    *,
    freshness: DataFreshness,
    start_utc: datetime,
    end_utc: datetime,
) -> str | None:
    latest = freshness.latest_event_at
    if latest is None or freshness.stored_event_count == 0:
        return None
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=UTC)
    else:
        latest = latest.astimezone(UTC)
    if latest < start_utc or latest > end_utc:
        return (
            "The table time filter excludes the latest observed activity in this scope. "
            "Freshness above reflects all stored events for the selected customer/site/sensor."
        )
    return None


def _apply_default_time_window(default_start: datetime, default_end: datetime) -> None:
    st.session_state["ne_start_utc"] = default_start
    st.session_state["ne_end_utc"] = default_end


def _reset_filters(default_start: datetime, default_end: datetime) -> None:
    st.session_state["ne_customer_id"] = None
    st.session_state["ne_site_id"] = None
    st.session_state["ne_sensor_id"] = None
    st.session_state["ne_page"] = 1
    st.session_state["ne_selected_event_id"] = None
    _apply_default_time_window(default_start, default_end)
    st.session_state.pop("ne_last_good", None)


def _db_unavailable(message: str) -> None:
    st.error(message)
    if st.button("Retry connection", type="primary", key="ne_retry_db"):
        st.rerun()


def render() -> None:
    settings = get_settings()
    try:
        msp_id = require_viewer_msp_id(settings.bluesentra_viewer_msp_id)
    except ViewerConfigError as exc:
        render_page_intro(
            title="Network Overview",
            subtitle="Review connection activity across customers and sites, then inspect individual connections.",
        )
        st.warning(str(exc))
        st.info(
            "Set `BLUESENTRA_VIEWER_MSP_ID` in `.env`, then restart Streamlit. "
            "This viewer reads PostgreSQL telemetry for one configured MSP only."
        )
        return

    if "ne_last_refresh" not in st.session_state:
        st.session_state["ne_last_refresh"] = None
    if "ne_page" not in st.session_state:
        st.session_state["ne_page"] = 1
    if "ne_page_size" not in st.session_state:
        st.session_state["ne_page_size"] = 25
    if "ne_selected_event_id" not in st.session_state:
        st.session_state["ne_selected_event_id"] = None

    render_page_intro(
        title="Network Overview",
        subtitle="Review connection activity across customers and sites, then inspect individual connections.",
    )

    try:
        db = get_session_factory()()
        try:
            customers = list_customers(db, msp_id=msp_id)
            bounds = get_event_time_bounds(db, msp_id=msp_id)
            total_imported = msp_event_count(db, msp_id=msp_id)
        finally:
            db.close()
    except SQLAlchemyError:
        _db_unavailable(
            "PostgreSQL is unavailable. Start the database with `docker compose up -d db` "
            "and confirm DATABASE_URL is configured."
        )
        return

    default_start, default_end = default_time_window(bounds)
    if "ne_start_utc" not in st.session_state:
        _apply_default_time_window(default_start, default_end)
    if "ne_customer_id" not in st.session_state:
        st.session_state["ne_customer_id"] = None
    if "ne_site_id" not in st.session_state:
        st.session_state["ne_site_id"] = None
    if "ne_sensor_id" not in st.session_state:
        st.session_state["ne_sensor_id"] = None

    customer_options = {ALL_CUSTOMERS: None}
    customer_options.update({c.label: str(c.id) for c in customers})

    with st.container(border=True):
        st.markdown('<p class="bs-section-label">Scope and time</p>', unsafe_allow_html=True)
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            customer_label = st.selectbox("Customer", list(customer_options.keys()))
        selected_customer = customer_options[customer_label]

        if selected_customer != st.session_state["ne_customer_id"]:
            st.session_state["ne_customer_id"] = selected_customer
            st.session_state["ne_site_id"] = None
            st.session_state["ne_sensor_id"] = None
            st.session_state["ne_page"] = 1
            st.session_state["ne_selected_event_id"] = None

        customer_uuid = uuid.UUID(selected_customer) if selected_customer else None

        try:
            db = get_session_factory()()
            try:
                sites = list_sites(db, msp_id=msp_id, customer_id=customer_uuid)
            finally:
                db.close()
        except SQLAlchemyError:
            _db_unavailable("Unable to load sites from PostgreSQL.")
            return

        site_options = {ALL_SITES: None}
        site_options.update({s.label: str(s.id) for s in sites})

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            site_label = st.selectbox("Site", list(site_options.keys()))
        selected_site = site_options[site_label]

        if selected_site != st.session_state["ne_site_id"]:
            st.session_state["ne_site_id"] = selected_site
            st.session_state["ne_sensor_id"] = None
            st.session_state["ne_page"] = 1
            st.session_state["ne_selected_event_id"] = None

        site_uuid = uuid.UUID(selected_site) if selected_site else None

        try:
            db = get_session_factory()()
            try:
                sensors = list_sensors(db, msp_id=msp_id, site_id=site_uuid)
            finally:
                db.close()
        except SQLAlchemyError:
            _db_unavailable("Unable to load sensors from PostgreSQL.")
            return

        sensor_options = {ALL_SENSORS: None}
        sensor_options.update({s.label: str(s.id) for s in sensors})
        with row2_col2:
            sensor_label = st.selectbox("Sensor", list(sensor_options.keys()))
        selected_sensor = sensor_options[sensor_label]
        if selected_sensor != st.session_state["ne_sensor_id"]:
            st.session_state["ne_sensor_id"] = selected_sensor
            st.session_state["ne_page"] = 1
            st.session_state["ne_selected_event_id"] = None
        st.session_state["ne_sensor_id"] = selected_sensor

        st.markdown('<p class="bs-section-label">Time range (UTC)</p>', unsafe_allow_html=True)
        start_default = st.session_state["ne_start_utc"]
        end_default = st.session_state["ne_end_utc"]
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            start_date = st.date_input("Start date", value=start_default.date())
        with t2:
            start_time = st.time_input("Start time", value=start_default.time())
        with t3:
            end_date = st.date_input("End date", value=end_default.date())
        with t4:
            end_time = st.time_input("End time", value=end_default.time())

        start_utc = datetime.combine(start_date, start_time, tzinfo=UTC)
        end_utc = datetime.combine(end_date, end_time, tzinfo=UTC)
        st.session_state["ne_start_utc"] = start_utc
        st.session_state["ne_end_utc"] = end_utc

        filter_fingerprint = (
            selected_customer,
            selected_site,
            selected_sensor,
            start_utc.isoformat(),
            end_utc.isoformat(),
        )
        if st.session_state.get("ne_filter_fingerprint") != filter_fingerprint:
            st.session_state["ne_filter_fingerprint"] = filter_fingerprint
            st.session_state["ne_page"] = 1
            st.session_state["ne_selected_event_id"] = None

        btn_reset, btn_help = st.columns([1, 3])
        with btn_reset:
            if st.button("Reset filters", help="Restore all-available scope and the default UTC window."):
                _reset_filters(default_start, default_end)
                st.rerun()
        with btn_help:
            st.caption(
                f"Default window: {default_start.strftime('%Y-%m-%d %H:%M')} → "
                f"{default_end.strftime('%Y-%m-%d %H:%M')} UTC (from imported event bounds)."
            )

    page_size = int(st.session_state["ne_page_size"])
    page = int(st.session_state["ne_page"])

    utc_window = (
        f"{start_utc.strftime('%Y-%m-%d %H:%M')} → {end_utc.strftime('%Y-%m-%d %H:%M')}"
    )

    refresh_clicked = render_context_bar(
        customer=customer_label,
        site=site_label,
        sensor=sensor_label,
        utc_window=utc_window,
        last_refresh=st.session_state["ne_last_refresh"],
    )
    if refresh_clicked:
        st.rerun()

    tenant_scope = TenantScope(
        customer_id=customer_uuid,
        site_id=site_uuid,
        sensor_id=uuid.UUID(selected_sensor) if selected_sensor else None,
    )
    table_filters = EventViewFilters(
        customer_id=tenant_scope.customer_id,
        site_id=tenant_scope.site_id,
        sensor_id=tenant_scope.sensor_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    data_fingerprint = (
        selected_customer,
        selected_site,
        selected_sensor,
        start_utc.isoformat(),
        end_utc.isoformat(),
        page,
        page_size,
    )

    payload: dict[str, Any] | None = None
    freshness: DataFreshness | None = None
    showing_stale = False
    try:
        with st.spinner("Loading connection events…"):
            payload = _load_view_data(
                msp_id=msp_id,
                filters=table_filters,
                page=page,
                page_size=page_size,
            )
            freshness = _load_freshness(msp_id=msp_id, scope=tenant_scope)
        st.session_state["ne_last_good"] = {
            "fingerprint": data_fingerprint,
            "payload": payload,
            "freshness": freshness,
        }
        st.session_state["ne_last_refresh"] = datetime.now(tz=UTC)
    except ViewerConfigError as exc:
        st.warning(str(exc))
        return
    except SQLAlchemyError:
        prior = st.session_state.get("ne_last_good")
        if prior and prior.get("fingerprint") == data_fingerprint:
            payload = prior["payload"]
            freshness = prior["freshness"]
            showing_stale = True
        else:
            _db_unavailable("Unable to query PostgreSQL for connection events.")
            return

    if payload is None or freshness is None:
        return

    if showing_stale:
        st.warning(
            "Showing previously loaded data from the last successful refresh. "
            "The latest reload failed."
        )

    ev_disp, ev_age, ing_disp, ing_age = _freshness_displays(freshness)
    render_data_freshness_panel(
        scope_label=_scope_label(customer_label, site_label, sensor_label),
        latest_event_display=ev_disp,
        latest_event_age=ev_age,
        latest_ingestion_display=ing_disp,
        latest_ingestion_age=ing_age,
        table_filter_note=_table_filter_excludes_latest(
            freshness=freshness,
            start_utc=start_utc,
            end_utc=end_utc,
        ),
    )
    summary = payload["summary"]
    total = payload["total"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(
            "Connection events",
            f"{summary.connection_count:,}",
            ICON_LINK,
            help_text="Normalized Zeek conn.log records matching the current filters.",
        )
    with m2:
        render_metric_card(
            "Distinct source IPs",
            f"{summary.distinct_src_ip_count:,}",
            ICON_GLOBE,
            help_text="Unique originator IP addresses in the filtered set.",
        )
    with m3:
        render_metric_card(
            "Originator bytes",
            format_bytes(summary.total_orig_bytes),
            ICON_UP,
            help_text=f"Sum of Zeek orig_bytes. {BYTE_UNITS_NOTE}",
        )
    with m4:
        render_metric_card(
            "Responder bytes",
            format_bytes(summary.total_resp_bytes),
            ICON_DOWN,
            help_text=f"Sum of Zeek resp_bytes. {BYTE_UNITS_NOTE}",
        )

    st.markdown(
        f'<p class="bs-help">{html.escape(BYTE_UNITS_NOTE)} '
        "Summaries describe connection telemetry only—not threat scores or device inventory.</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<p class="bs-section-title">Connection activity</p>', unsafe_allow_html=True)
    st.caption(f"{total:,} matching events · sorted newest first · all times UTC")

    if total_imported == 0:
        st.info(
            "No connection events have been imported for this MSP yet. "
            "Import Zeek conn.log JSONL with the project CLI, then refresh."
        )
        return

    if summary.connection_count == 0:
        st.warning(
            "No events match the current filters. Try widening the UTC window, choosing "
            "all available sites or sensors, or reset filters to the default window."
        )
        if st.button("Reset filters and retry", key="ne_reset_empty"):
            _reset_filters(default_start, default_end)
            st.rerun()
        return

    rows = payload["rows"]
    table = pd.DataFrame(
        [
            {
                "Event time (UTC)": r.event_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "Sensor": r.sensor_name,
                "Source IP": r.src_ip,
                "Src port": _fmt_port(r.src_port),
                "Destination IP": r.dst_ip,
                "Dst port": _fmt_port(r.dst_port),
                "Protocol": r.transport_protocol.upper(),
                "Service": r.service if r.service else "—",
                "Orig bytes": format_bytes(r.orig_bytes),
                "Resp bytes": format_bytes(r.resp_bytes),
                "Duration (s)": _fmt_duration(r.duration),
            }
            for r in rows
        ]
    )

    mono_cols = ["Source IP", "Destination IP"]
    try:
        table_to_show = table.style.set_properties(
            subset=mono_cols,
            **{"font-family": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"},
        )
    except Exception:
        table_to_show = table

    with st.container(border=True):
        st.dataframe(
            table_to_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Event time (UTC)": st.column_config.TextColumn(
                    "Event time (UTC)",
                    help="Connection event timestamp in UTC",
                ),
                "Source IP": st.column_config.TextColumn("Source IP"),
                "Destination IP": st.column_config.TextColumn("Destination IP"),
                "Orig bytes": st.column_config.TextColumn("Orig bytes"),
                "Resp bytes": st.column_config.TextColumn("Resp bytes"),
                "Protocol": st.column_config.TextColumn("Protocol"),
            },
        )

    total_pages = max(1, (total + page_size - 1) // page_size)
    nav1, nav2, nav3, nav4 = st.columns([1, 1, 2, 1])
    with nav1:
        if st.button(
            "Previous page",
            disabled=page <= 1,
            key="ne_prev_page",
            help="Go to the previous page of results",
        ):
            st.session_state["ne_page"] = max(1, page - 1)
            st.session_state["ne_selected_event_id"] = None
            st.rerun()
    with nav2:
        if st.button(
            "Next page",
            disabled=page >= total_pages,
            key="ne_next_page",
            help="Go to the next page of results",
        ):
            st.session_state["ne_page"] = min(total_pages, page + 1)
            st.session_state["ne_selected_event_id"] = None
            st.rerun()
    with nav3:
        st.caption(
            f"Page {page} of {total_pages} · showing {len(rows)} row(s) on this page"
        )
    with nav4:
        new_size = st.selectbox(
            "Rows per page",
            [10, 25, 50],
            index=[10, 25, 50].index(page_size) if page_size in (10, 25, 50) else 1,
        )
        if int(new_size) != page_size:
            st.session_state["ne_page_size"] = int(new_size)
            st.session_state["ne_page"] = 1
            st.session_state["ne_selected_event_id"] = None
            st.rerun()

    event_ids = [str(r.id) for r in rows]
    id_labels = {str(r.id): _row_label(r) for r in rows}
    if st.session_state["ne_selected_event_id"] not in event_ids:
        st.session_state["ne_selected_event_id"] = None

    default_index = 0
    if st.session_state["ne_selected_event_id"] in event_ids:
        default_index = event_ids.index(st.session_state["ne_selected_event_id"])

    st.markdown('<p class="bs-section-title">Connection details</p>', unsafe_allow_html=True)
    picked_id = st.selectbox(
        "Select a connection from this page",
        event_ids,
        index=default_index,
        format_func=lambda eid: id_labels[eid],
        help="Selection uses the immutable event UUID. Clears when filters or page change.",
    )
    st.session_state["ne_selected_event_id"] = picked_id

    try:
        detail = _load_event_detail(
            msp_id=msp_id,
            event_id=uuid.UUID(picked_id),
            filters=table_filters,
        )
    except SQLAlchemyError:
        _db_unavailable("Unable to load connection details from PostgreSQL.")
        return

    if detail is None:
        st.warning("This connection is unavailable for the current filters or may have been removed.")
        st.session_state["ne_selected_event_id"] = None
        return

    with st.container(border=True):
        _render_connection_detail(detail)
