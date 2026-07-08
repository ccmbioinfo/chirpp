import streamlit as st
import pandas as pd
from chirpp_ui.utils.classes import *

# --- 1. Session State Initialization ---
# Ensure the admin page doesn't crash if accessed directly
if "pending_resets" not in st.session_state:
    st.session_state.pending_resets = set()

db = st.session_state.database
user = st.session_state.user


# --- 2. Dialogs (Modals) ---

@st.dialog("Create New User", width="small")
def create_user_dialog():
    st.write("Register a new team member.")
    f = st.text_input("First Name")
    l = st.text_input("Last Name")
    e = st.text_input("Email")
    if st.button("Generate Account", type="primary", width="stretch"):
        if f and l and e:
            temp_pw = user.add_user(f, l, e, db)
            st.success(f"User Created! **Temp Password: {temp_pw}**")
            if st.button("Done"): st.rerun()
        else:
            st.error("Please fill all fields.")


@st.dialog("Promote User to Manager")
def promote_user_dialog(user_to_promote):
    st.write(f"Assigning subordinates to **{user_to_promote['first_name']}**.")
    all_users = user.manages
    potential = [u for u in all_users if u['id'] != user_to_promote['id'] and user.is_active]

    selected = st.multiselect(
        "Select users to be managed by them:",
        options=potential,
        format_func=lambda u: f"{u['first_name']} {u['last_name']} ({u['email']})"
    )

    if st.button("Confirm Promotion", type="primary", use_container_width=True):
        if selected:
            sub_ids = [u['id'] for u in selected]
            user.promote_to_manager(user_to_promote['id'], sub_ids, db)
            st.toast(f"{user_to_promote['first_name']} promoted!")
            st.rerun()
        else:
            st.warning("Please select at least one subordinate.")


@st.dialog("Demote Manager")
def demote_user_dialog(manager_to_demote):
    st.warning(f"Are you sure you want to demote **{manager_to_demote['first_name']}**?")
    st.write("They will no longer be able to manage users, This action cannot be undone."
             "You will need to re-promote with all the subordinates.")
    if st.button("Yes, Demote", type="primary", use_container_width=True):
        user.demote_manager(manager_to_demote['id'], db)
        st.toast(f"{manager_to_demote['first_name']} demoted.")
        st.rerun()


# --- 3. The Main UI Fragment ---

@st.fragment
def render_admin_dashboard():
    st.title("Admin Dashboard")

    if not user.manages:
        st.info("You are not currently managing any users.")
        if st.button("➕ Add New User"): create_user_dialog()
        return

    # Table and Actions Layout
    df = pd.DataFrame(user.manages)

    col_df, col_actions = st.columns([2.5, 1.5])

    with col_df:
        st.subheader("Team Table")
        edited_df = st.data_editor(
            df,
            column_config={
                "user_id": None,
                "active": st.column_config.CheckboxColumn("Active"),
                "is_manager": st.column_config.CheckboxColumn("Manager", disabled=True),
            },
            disabled=["first_name", "last_name", "email", "is_manager"],
            hide_index=True,
            use_container_width=True,
            key="admin_editor"
        )

    with col_actions:
        st.subheader("Actions")
        # Add some vertical space to align with table header
        st.write("")
        for index, row in df.iterrows():
            c1, c2 = st.columns(2)
            u_id = row['id']

            # Reset Button
            is_pending = u_id in st.session_state.pending_resets
            c1.button("Reset", key=f"res_{u_id}", disabled=is_pending,
                      on_click=lambda id=u_id: st.session_state.pending_resets.add(id),
                      use_container_width=True)

            # Promote/Demote Toggle
            if row.get('is_manager', False):
                if c2.button("Demote", key=f"mgmt_{u_id}", use_container_width=True):
                    demote_user_dialog(row)
            else:
                if c2.button("Promote", key=f"mgmt_{u_id}", type="primary", use_container_width=True):
                    promote_user_dialog(row)

    st.divider()

    # Save & Utility Buttons
    footer_1, footer_2, footer_3 = st.columns([2, 1, 1])

    with footer_1:
        if st.button("💾 Save Activation & Resets", type="primary", use_container_width=True):
            # 1. Activation
            for _, r in edited_df.iterrows():
                user.update_activation_status(r['id'], r['active'], db)
            # 2. Resets
            for rid in st.session_state.pending_resets:
                user.reset_password(rid, db)

            st.session_state.pending_resets = set()
            st.success("Changes saved!")
            st.rerun(scope="app")

    with footer_2:
        if st.button("🗑️ Discard", use_container_width=True):
            st.session_state.pending_resets = set()
            st.rerun(scope="fragment")

    with footer_3:
        if st.button("➕ Add User", use_container_width=True):
            create_user_dialog()


# --- 4. Execution ---
render_admin_dashboard()