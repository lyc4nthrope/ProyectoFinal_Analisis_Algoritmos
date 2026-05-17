"""Vista de búsqueda en OpenAlex API.

Los resultados se guardan en un archivo JSONL en disco para no saturar
la RAM ni el session_state de Streamlit (que se serializa por WebSocket
en cada rerun). La vista de resultados se pagina de a 50 registros.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_sources import ApiParser

# ── Constantes ──────────────────────────────────────────────────────────────

MAX_AUTO_FETCH = 10_000
PAGE_SIZE = 50
RESULTS_FILE = Path("data/raw/api_cache") / "search_results.jsonl"
# Tiempo estimado por página (request + parse) en segundos
SECS_PER_PAGE = 2.0


# ── Helpers JSONL ───────────────────────────────────────────────────────────

def _cleanup() -> None:
    """Borra archivo temporal y todo el estado de búsqueda."""
    RESULTS_FILE.unlink(missing_ok=True)
    keys = [
        "api_result_count", "api_searching", "api_cursor",
        "api_total", "api_target", "api_first_fetch", "api_limit",
        "api_display_page", "api_selected_indices", "api_fetch_all",
        "api_confirm_total", "api_confirm_est", "api_query_value",
    ]
    for k in keys:
        st.session_state.pop(k, None)


def _append_jsonl(results: list[dict]) -> None:
    """Append resultados al archivo JSONL."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_jsonl_slice(start: int, count: int) -> list[dict]:
    """Lee un slice de resultados del JSONL sin cargar todo en memoria."""
    results = []
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < start:
                continue
            if len(results) >= count:
                break
            results.append(json.loads(line))
    return results


def _read_all_jsonl() -> list[dict]:
    """Lee TODOS los resultados del JSONL (solo para integrar al corpus)."""
    results = []
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
    return results


# ── Vista ───────────────────────────────────────────────────────────────────

def render() -> None:
    st.header("🔍 Búsqueda en OpenAlex")
    st.markdown("Busque artículos académicos en OpenAlex y agréguelos al corpus.")

    query = st.text_input(
        "Término de búsqueda",
        placeholder="Ej: machine learning, generative AI...",
        key="api_query",
    )

    col_slider, col_check = st.columns([3, 1])
    with col_slider:
        max_results = st.slider(
            "Cantidad de resultados",
            min_value=5,
            max_value=500,
            value=25,
            step=5,
            key="api_max_results",
        )
    with col_check:
        fetch_all = st.checkbox(
            "Buscar todos\ndisponibles",
            key="api_fetch_all",
            help="Trae TODOS los resultados disponibles (sin límite). Se paganiza de 200 en 200.",
        )

    # ── Botón de búsqueda ──────────────────────────────────────────────
    if st.button("🔍 Buscar en OpenAlex", type="primary"):
        q = (query or "").strip()
        if not q:
            st.warning("⚠️ Ingrese un término de búsqueda.")
        else:
            # Si pidió "todos", primero averiguamos cuántos hay con una
            # llamada rápida (?per_page=1) y mostramos confirmación si
            # supera un umbral.
            if fetch_all:
                parser = ApiParser()
                try:
                    quick = parser.fetch_page(q, "*", 1)
                except Exception as e:
                    st.error(f"❌ No se pudo conectar con OpenAlex: {e}")
                    st.stop()

                total_avail = quick["total"]
                # Ya tenemos la primera página, la guardamos
                _cleanup()
                _append_jsonl(quick["results"])
                st.session_state.api_result_count = len(quick["results"])
                st.session_state.api_total = total_avail
                st.session_state.api_cursor = quick.get("next_cursor")
                st.session_state.api_limit = max_results
                st.session_state.api_first_fetch = False  # ya la hicimos
                st.session_state.api_display_page = 0
                st.session_state.api_selected_indices = set()
                st.session_state.api_query_value = q

                if total_avail > 2_000:
                    est_min = (total_avail / 200) * SECS_PER_PAGE / 60
                    st.session_state.api_confirm_total = total_avail
                    st.session_state.api_confirm_est = f"{est_min:.0f}"
                    st.session_state.api_fetch_all = True
                    # No arrancamos la descarga completa todavía
                else:
                    # Poco volumen, arrancamos derecho
                    st.session_state.api_target = total_avail
                    st.session_state.api_fetch_all = True
                    st.session_state.api_searching = True
                    st.session_state.api_first_fetch = False
                    st.rerun()
            else:
                # Búsqueda con límite fijo — arrancamos sin confirmación
                _cleanup()
                st.session_state.api_query_value = q
                st.session_state.api_searching = True
                st.session_state.api_result_count = 0
                st.session_state.api_cursor = "*"
                st.session_state.api_total = 0
                st.session_state.api_target = 0
                st.session_state.api_limit = max_results
                st.session_state.api_first_fetch = True
                st.session_state.api_fetch_all = False
                st.session_state.api_display_page = 0
                st.session_state.api_selected_indices = set()
                st.rerun()

    # ── Confirmación de volumen grande ─────────────────────────────────
    if st.session_state.get("api_confirm_total") and not st.session_state.get("api_searching"):
        total = st.session_state.api_confirm_total
        est = st.session_state.api_confirm_est
        st.warning(
            f"⚠️ Hay **{total:,}** resultados disponibles en OpenAlex. "
            f"Tiempo estimado: **~{est} minutos**.",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, buscar todos"):
                st.session_state.api_target = total
                st.session_state.api_searching = True
                st.session_state.pop("api_confirm_total", None)
                st.session_state.pop("api_confirm_est", None)
                # Si ya tenemos la primera página, empezamos desde el cursor
                st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                _cleanup()
                st.info("Búsqueda cancelada. Se conservan los primeros resultados obtenidos.")
                # Los primeros resultados (per_page=1) no son útiles,
                # mejor limpiar todo
                RESULTS_FILE.unlink(missing_ok=True)
                st.rerun()

    # ── Bucle de paginación ──────────────────────────────────────────
    if st.session_state.get("api_searching"):
        st.warning("⏳ Buscando...", icon="🔄")

        if st.button("🛑 Detener búsqueda"):
            st.session_state.api_searching = False
            st.rerun()

        # Barra de progreso ANTES de la API call
        loaded_sofar = st.session_state.get("api_result_count", 0)
        target = st.session_state.get("api_target", 0)
        progress_placeholder = st.empty()
        if loaded_sofar == 0 and target == 0:
            progress_placeholder.progress(0, text="🌐 Iniciando búsqueda...")
        else:
            pct = min(loaded_sofar / target, 1.0) if target > 0 else 0
            progress_placeholder.progress(
                pct,
                text=f"Buscando... {loaded_sofar:,} de {target:,} resultados "
                     f"(total en OpenAlex: {st.session_state.get('api_total', 0):,})",
            )

        parser = ApiParser()
        try:
            data = parser.fetch_page(
                st.session_state.api_query_value,
                st.session_state.api_cursor,
                200,
            )
        except Exception as e:
            st.error(f"❌ {e}")
            st.session_state.api_searching = False
            st.rerun()

        if st.session_state.pop("api_first_fetch", False):
            total_avail = data["total"]
            if st.session_state.get("api_fetch_all"):
                target = total_avail
            else:
                target = min(st.session_state.api_limit, total_avail)
            st.session_state.api_total = total_avail
            st.session_state.api_target = target

        new_results = data["results"]
        _append_jsonl(new_results)
        st.session_state.api_result_count = (
            st.session_state.get("api_result_count", 0) + len(new_results)
        )
        st.session_state.api_cursor = data["next_cursor"]

        loaded = st.session_state.api_result_count
        target = st.session_state.api_target

        pct = min(loaded / target, 1.0) if target > 0 else 0
        progress_placeholder.progress(
            pct,
            text=f"Buscando... {loaded:,} de {target:,} resultados "
                 f"(total en OpenAlex: {st.session_state.api_total:,})",
        )

        has_more = bool(data.get("next_cursor"))
        limit_ok = loaded >= target

        if not has_more or limit_ok:
            st.session_state.api_searching = False
            st.rerun()
        else:
            st.rerun()

    st.divider()

    # ── Resultados paginados ───────────────────────────────────────────
    if (RESULTS_FILE.exists()
            and st.session_state.get("api_result_count", 0) > 0
            and not st.session_state.get("api_searching")):

        total_fetched = st.session_state.api_result_count
        total_in_oa = st.session_state.get("api_total", 0)
        st.subheader(f"Mostrando {total_fetched:,} de {total_in_oa:,} resultados")

        # Selección global y paginación
        total_pages = max(1, (total_fetched + PAGE_SIZE - 1) // PAGE_SIZE)
        page = st.session_state.get("api_display_page", 0)
        page = min(page, total_pages - 1)

        col_all, col_none, col_prev, col_info, col_next = st.columns([1, 1, 1, 2, 1])
        with col_all:
            if st.button(f"☑️ Todo ({total_fetched:,})"):
                st.session_state.api_selected_indices = set(range(total_fetched))
                st.rerun()
        with col_none:
            if st.button("🗑️ Ninguno"):
                st.session_state.api_selected_indices = set()
                st.rerun()
        with col_prev:
            if page > 0 and st.button("← Anterior"):
                st.session_state.api_display_page = page - 1
                st.rerun()
        with col_info:
            st.caption(f"Página {page + 1} de {total_pages}")
        with col_next:
            if page < total_pages - 1 and st.button("Siguiente →"):
                st.session_state.api_display_page = page + 1
                st.rerun()

        # Leer SOLO la página actual del archivo
        start = page * PAGE_SIZE
        page_results = _read_jsonl_slice(start, PAGE_SIZE)

        df = pd.DataFrame(page_results)
        display_cols = {
            "title": "Título",
            "authors": "Autores",
            "year": "Año",
            "doi": "DOI",
            "journal": "Revista/Fuente",
        }
        available_cols = {k: v for k, v in display_cols.items() if k in df.columns}
        df_display = df[list(available_cols.keys())].copy()
        df_display.columns = list(available_cols.values())

        # Pre-fill selection desde session_state
        selected = st.session_state.get("api_selected_indices", set())
        df_display["seleccionar"] = [(start + i) in selected for i in range(len(df_display))]

        edited = st.data_editor(
            df_display,
            column_config={
                "seleccionar": st.column_config.CheckboxColumn(
                    "Sel.",
                    default=False,
                    width="small",
                ),
            },
            column_order=["seleccionar"] + list(available_cols.values()),
            hide_index=True,
            use_container_width=True,
            height=400,
        )

        # Persistir selecciones desde el editor
        new_selected = set(st.session_state.get("api_selected_indices", set()))
        for i, sel in enumerate(edited.get("seleccionar", [])):
            idx = start + i
            if sel:
                new_selected.add(idx)
            else:
                new_selected.discard(idx)
        st.session_state.api_selected_indices = new_selected

        selected_count = len(new_selected)
        if selected_count > 0:
            st.caption(f"{selected_count} resultado(s) seleccionado(s)")

        if selected_count > 0:
            if st.button("📥 Integrar al corpus", type="primary"):
                all_results = _read_all_jsonl()
                selected_results = [
                    r for i, r in enumerate(all_results) if i in new_selected
                ]

                if not selected_results:
                    st.warning("Seleccioná al menos un artículo para integrar.")
                else:
                    processed_dir = Path("data/processed")
                    processed_dir.mkdir(parents=True, exist_ok=True)
                    path = processed_dir / "unified.csv"

                    nuevos = pd.DataFrame(selected_results)
                    if path.exists():
                        existentes = pd.read_csv(path)
                        corpus = pd.concat([existentes, nuevos], ignore_index=True)
                        corpus = corpus.drop_duplicates(subset="doi", keep="first")
                    else:
                        corpus = nuevos

                    corpus.to_csv(path, index=False, quoting=1)
                    total_corpus = len(corpus)

                    st.cache_data.clear()
                    st.cache_resource.clear()

                    _cleanup()

                    st.success(
                        f"✅ {len(selected_results)} artículo(s) integrado(s). "
                        f"Corpus actualizado: {total_corpus} artículo(s) en total."
                    )
                    st.rerun()
