"""Vista de búsqueda en OpenAlex API."""

# Importa pandas para construir el DataFrame de resultados mostrado al usuario
import pandas as pd
# Importa Streamlit para construir la interfaz de búsqueda
import streamlit as st

# Importa la función que integra artículos seleccionados al corpus local
from src.repositories import integrate_articles
# Importa el servicio de búsqueda y el almacén temporal de resultados
from src.services import ApiSearchService, ApiSearchStore

# ── Constantes ──────────────────────────────────────────────────────────────

# Cantidad de resultados por página en la tabla de resultados de la UI
PAGE_SIZE = 50
# Tiempo estimado por página (request + parse) en segundos
SECS_PER_PAGE = 2.0
# Instancia global del almacén JSONL para resultados temporales de búsqueda
STORE = ApiSearchStore()
# Instancia global del servicio que llama a la API de OpenAlex
SERVICE = ApiSearchService()


# ── Helpers estado ──────────────────────────────────────────────────────────

def _cleanup() -> None:
    """Borra resultados temporales y todo el estado de búsqueda."""
    # Limpia el archivo JSONL temporal con los resultados de la búsqueda anterior
    STORE.clear()
    # Lista de todas las claves de session_state relacionadas con la búsqueda
    keys = [
        "api_result_count", "api_searching", "api_cursor",
        "api_total", "api_target", "api_first_fetch", "api_limit",
        "api_display_page", "api_selected_indices", "api_fetch_all",
        "api_confirm_total", "api_confirm_est", "api_query_value",
    ]
    # Elimina cada clave del session_state si existe (pop no lanza error si falta)
    for k in keys:
        st.session_state.pop(k, None)

# ── Vista ───────────────────────────────────────────────────────────────────

def render() -> None:
    st.header("🔍 Búsqueda en OpenAlex")
    st.markdown("Busque artículos académicos en OpenAlex y agréguelos al corpus.")

    # Campo de texto para ingresar el término de búsqueda
    query = st.text_input(
        "Término de búsqueda",
        placeholder="Ej: machine learning, generative AI...",
        key="api_query",
    )

    # Dos columnas: slider de cantidad de resultados y checkbox "buscar todos"
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
                try:
                    # Llama con per_page=1 solo para obtener el total disponible
                    quick = SERVICE.fetch_total_preview(q)
                except Exception as e:
                    st.error(f"❌ No se pudo conectar con OpenAlex: {e}")
                    return

                total_avail = quick["total"]
                # Guarda la primera página que ya vino en la respuesta preview
                _cleanup()
                STORE.append(quick["results"])
                st.session_state.api_result_count = len(quick["results"])
                st.session_state.api_total = total_avail
                st.session_state.api_cursor = quick.get("next_cursor")
                st.session_state.api_limit = max_results
                st.session_state.api_first_fetch = False  # ya la hicimos
                st.session_state.api_display_page = 0
                st.session_state.api_selected_indices = set()
                st.session_state.api_query_value = q

                if total_avail > 2_000:
                    # Volumen grande: calcular estimado y pedir confirmación del usuario
                    est_min = (total_avail / 200) * SECS_PER_PAGE / 60
                    st.session_state.api_confirm_total = total_avail
                    st.session_state.api_confirm_est = f"{est_min:.0f}"
                    st.session_state.api_fetch_all = True
                    # No arrancamos la descarga completa todavía
                else:
                    # Poco volumen, arrancamos derecho sin confirmación
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
    # Muestra advertencia y botones de confirmación si el total supera 2000 resultados
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
                # El usuario confirmó: arrancar la descarga completa
                st.session_state.api_target = total
                st.session_state.api_searching = True
                st.session_state.pop("api_confirm_total", None)
                st.session_state.pop("api_confirm_est", None)
                # Si ya tenemos la primera página, empezamos desde el cursor guardado
                st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                # El usuario canceló: limpiar todo el estado
                _cleanup()
                st.info("Búsqueda cancelada. Se limpiaron los resultados temporales.")
                st.rerun()

    # ── Bucle de paginación ──────────────────────────────────────────
    # Este bloque ejecuta una página por rerun de Streamlit: fetch → guarda → rerun
    if st.session_state.get("api_searching"):
        st.warning("⏳ Buscando...", icon="🔄")

        # Botón para detener la descarga en cualquier momento
        if st.button("🛑 Detener búsqueda"):
            st.session_state.api_searching = False
            st.rerun()

        # Barra de progreso ANTES de la API call para dar feedback inmediato
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

        try:
            # Llama al servicio para obtener la siguiente página de resultados
            data = SERVICE.fetch_next_page(
                query=st.session_state.api_query_value,
                cursor=st.session_state.api_cursor,
                fetch_all=st.session_state.get("api_fetch_all", False),
                limit=st.session_state.get("api_limit", 0),
                loaded=loaded_sofar,
                target=target,
                first_fetch=st.session_state.get("api_first_fetch", False),
            )
        except Exception as e:
            # Error de red u otro — detiene la búsqueda y avisa al usuario
            st.error(f"❌ La búsqueda se pausó por un error: {e}")
            st.session_state.api_searching = False
            st.rerun()

        # Si el servicio indica que no hay más resultados, detiene la búsqueda
        if data is None:
            st.session_state.api_searching = False
            st.rerun()

        # En la primera página, actualiza el total disponible y el target real
        if st.session_state.pop("api_first_fetch", False):
            total_avail = data["total"]
            if st.session_state.get("api_fetch_all"):
                target = total_avail
            else:
                target = min(st.session_state.api_limit, total_avail)
            st.session_state.api_total = total_avail
            st.session_state.api_target = target

        # Guarda los resultados de esta página en el JSONL y actualiza el contador
        new_results = data["results"]
        STORE.append(new_results)
        st.session_state.api_result_count = (
            st.session_state.get("api_result_count", 0) + len(new_results)
        )
        st.session_state.api_cursor = data["next_cursor"]

        # Actualiza la barra de progreso con los valores post-fetch
        loaded = st.session_state.api_result_count
        target = st.session_state.api_target

        pct = min(loaded / target, 1.0) if target > 0 else 0
        progress_placeholder.progress(
            pct,
            text=f"Buscando... {loaded:,} de {target:,} resultados "
                 f"(total en OpenAlex: {st.session_state.api_total:,})",
        )

        # Decide si hay más páginas: sin cursor o ya se alcanzó el target → detener
        has_more = bool(data.get("next_cursor"))
        limit_ok = loaded >= target

        if not has_more or limit_ok:
            st.session_state.api_searching = False
            st.rerun()
        else:
            # Todavía hay más páginas — rerun para continuar el bucle
            st.rerun()

    st.divider()

    # ── Resultados paginados ───────────────────────────────────────────
    # Muestra los resultados solo cuando hay datos en el STORE y la búsqueda terminó
    if (STORE.exists()
            and st.session_state.get("api_result_count", 0) > 0
            and not st.session_state.get("api_searching")):

        total_fetched = st.session_state.api_result_count
        total_in_oa = st.session_state.get("api_total", 0)
        st.subheader(f"Mostrando {total_fetched:,} de {total_in_oa:,} resultados")

        # Calcula la página actual y el total de páginas con PAGE_SIZE=50
        total_pages = max(1, (total_fetched + PAGE_SIZE - 1) // PAGE_SIZE)
        page = st.session_state.get("api_display_page", 0)
        page = min(page, total_pages - 1)

        # Controles de navegación: seleccionar todo, ninguno, anterior, info, siguiente
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

        # Lee SOLO la página actual del JSONL — evita cargar todos los resultados en RAM
        start = page * PAGE_SIZE
        page_results = STORE.read_slice(start, PAGE_SIZE)

        # Construye el DataFrame solo con las columnas visibles al usuario
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

        # Rellena la columna "seleccionar" basándose en los índices globales guardados
        selected = st.session_state.get("api_selected_indices", set())
        df_display["seleccionar"] = [(start + i) in selected for i in range(len(df_display))]

        # Editor interactivo con checkbox por fila para que el usuario seleccione artículos
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
            width="stretch",
            height=400,
        )

        # Sincroniza las selecciones del editor de vuelta al session_state global
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

        # Botón de integración: solo aparece si hay artículos seleccionados
        if selected_count > 0:
            if st.button("📥 Integrar al corpus", type="primary"):
                # Lee todos los resultados del JSONL y filtra los seleccionados
                all_results = STORE.read_all()
                selected_results = [
                    r for i, r in enumerate(all_results) if i in new_selected
                ]

                if not selected_results:
                    st.warning("Seleccioná al menos un artículo para integrar.")
                else:
                    # Integra al corpus y obtiene la cantidad total de artículos
                    _, total_corpus = integrate_articles(selected_results)

                    # Limpia el caché de Streamlit para que el corpus se recargue
                    st.cache_data.clear()
                    st.cache_resource.clear()

                    # Limpia el estado de búsqueda temporal después de integrar
                    _cleanup()

                    st.success(
                        f"✅ {len(selected_results)} artículo(s) integrado(s). "
                        f"Corpus actualizado: {total_corpus} artículo(s) en total."
                    )
                    st.rerun()
