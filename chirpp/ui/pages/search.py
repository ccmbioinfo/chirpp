from datetime import date
import streamlit as st
from streamlit import column_config

from chirpp.ui.utils.database import *

st.set_page_config(layout="wide")

def search_db(query):
    pass

def has_active_filters(d):
    """Returns True if there is at least one value deep inside the dict."""
    return any(
        any(
            any(vals for vals in comps.values())
            for comps in cols.values()
        )
        for cols in d.values()
    )

def get_label(opt):
    return SYMBOL_MAP.get(opt, opt)

def get_table_label(key):
    if key == "-- Select Table --": return key
    return TABLE_CONFIG.get(key, {}).get("label", key)

def get_col_label(key, table_key):
    cols = TABLE_CONFIG.get(table_key, {}).get("columns", {})
    return str(cols.get(key, {}).get("label", key))


if "filters" not in st.session_state:
    st.session_state.filters = {}

if "filter_history" not in st.session_state:
    st.session_state.filter_history = []

st.title("Search")
st.markdown("#### Keyword Search")
s11, negative, positive, key_table, s12 = st.columns([1,3,3,2,1])

with negative:
    st.text_input("Enter terms to avoid in the search separated by commas",
                  placeholder="Enter terms to avoid", key="neg_keywords")

with positive:
    st.text_input("Enter terms to look for separated by commas",
                  placeholder="Enter terms to find", key="pos_keywords")

with key_table:
    st.selectbox("Search in:", ["PHAC Summaries", "SK Narrative(Slower)", "Full Notes (Slow)"])

st.markdown("#### Semantic Search")
s21, semantic, sem_table, s22 = st.columns([1, 6, 2, 1])

with semantic:
    st.text_input("Enter the description of the cases you are looking for",
                  placeholder="Description goes here", key="semantic")
with sem_table:
    st.selectbox("Search in:", ["PHAC Summaries", "Triage and Provider Notes", "Full Notes (Slow)"])

st.markdown("#### Table Filters")
s31, col1, col2, col3, col4, s32 = st.columns([1, 2, 2, 2, 2, 1])

column_selected=False
comparator_selected=False

with col1:
    with col1:
        table = st.selectbox(
            "Table",
            ["-- Select Table --"] + list(TABLE_CONFIG.keys()),
            format_func=get_table_label
        )

    table_selected = table != "-- Select Table --"

    with col2:
        if table_selected:
            # Note: Accessing .get("columns") now because of the new nesting
            column_options = list(TABLE_CONFIG[table]["columns"].keys())
            column = st.selectbox(
                "Column",
                ["-- Select Column --"] + column_options,
                format_func=lambda x: get_col_label(x, table)
            )
            column_selected=column != "-- Select Column --"
        else:
            column = st.selectbox("Column", [], disabled=True)

    with col3:
        if column_selected:
            column_config = TABLE_CONFIG[table]["columns"][column]

            with col3:
                if column_selected:
                # Use format_func to show signs instead of text keys
                    comparator = st.selectbox(
                        "Comparator",
                        ["-- Select Comparison --"]+ column_config["comparators"],
                        format_func=get_label
                    )
                    comparator_selected=comparator != "-- Select Comparison --"
                else:
                    comparator = st.selectbox("Comparator", [], disabled=True)


    with col4:
        if comparator_selected:
        # Value Input Logic
            if comparator in ["like", "not_like"]:
                value = st.text_input("Search Term", placeholder="e.g. fracture")

            elif column_config["type"] == "categorical":
                values = column_config.get("values", [])
                code_labels = column_config.get("code_labels", {})
                is_multi = comparator in ["in", "not_in"]

                display_map = {f"{c} - {code_labels.get(c, '')}": c for c in values}
                display_options = list(display_map.keys())

                if is_multi:
                    selected = st.multiselect("Search & Select Values", display_options)
                    value = [display_map[s] for s in selected]
                else:
                    # selectbox already acts as a 'selectize' search box in Streamlit
                    selected = st.selectbox("Search Value", display_options)
                    value = display_map[selected]


            elif column_config["type"] in ["numeric", "numerical"]:
                value = st.number_input("Value", value=0)
            elif column_config["type"] == "date":
                value = str(st.date_input("Value", date(2020, 1, 1)))

    if st.button("Add Filter"):
        # 1. Identify if it's a virtual column
        is_virtual = "virtual_group" in column_config
        target_columns = column_config.get("virtual_group", [column])

        # 2. Initialize the dictionary structure
        st.session_state.filters.setdefault(table, {})
        st.session_state.filters[table].setdefault(column, {})

        # We store values in a list to allow "Fracture" AND "Abrasion" for the same column
        if comparator not in st.session_state.filters[table][column]:
            st.session_state.filters[table][column][comparator] = []

        # 3. Add the value if it's not a duplicate
        if value in st.session_state.filters[table][column][comparator]:
            st.warning(f"'{value}' is already in this filter.")
        else:
            st.session_state.filters[table][column][comparator].append(value)

            # 4. Add to history for the UI display
            st.session_state.filter_history.append({
                "table": table,
                "column": column,  # The key (e.g., 'sd_all')
                "real_cols": target_columns,  # The actual DB columns (e.g., ['sd1', 'sd2'...])
                "comparator": comparator,
                "value": value,
                "is_virtual": is_virtual
            })
            st.toast(f"Added {value} to {column_config['label']}")


st.subheader("Current Filters")
if not st.session_state.filter_history:
    st.info("No filters added.")
else:
    for i, f in enumerate(st.session_state.filter_history):
        row = st.columns([6, 1])
        with row[0]:
            t_label = get_table_label(f['table'])
            c_label = get_col_label(f['column'], f['table'])
            comp_sign = get_label(f['comparator'])

            st.write(f"**{t_label}** → {c_label} {comp_sign} `{f['value']}`")

        with row[1]:
            if st.button("❌", key=f"delete_{i}"):
                f = st.session_state.filter_history[i]
                t_name = f["table"]
                c_name = f["column"]
                comp = f["comparator"]
                val = f["value"]

                if t_name in st.session_state.filters:
                    if c_name in st.session_state.filters[t_name]:
                        if comp in st.session_state.filters[t_name][c_name]:
                            st.session_state.filters[t_name][c_name][comp].remove(val)

                            if not st.session_state.filters[t_name][c_name][comp]:
                                del st.session_state.filters[t_name][c_name][comp]

                        if not st.session_state.filters[t_name][c_name]:
                            del st.session_state.filters[t_name][c_name]

                    if not st.session_state.filters[t_name]:
                        del st.session_state.filters[t_name]

                st.session_state.filter_history.pop(i)
                st.rerun()

st.divider()
c_btn, _ = st.columns([2, 6])
with c_btn:
    if st.button("Search Database", use_container_width=True, type="primary"):
        if has_active_filters(st.session_state.filters):
            results = st.session_state.query.search_db(st.session_state.filters)
        else:
            st.error("Your filter list is empty. Please add a filter first.")

