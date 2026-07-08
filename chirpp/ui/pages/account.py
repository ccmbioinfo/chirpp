import bcrypt
import streamlit as st

left, middle, right = st.columns([1, 10, 1])

st.session_state.setdefault("toast_msg", "")
st.session_state.setdefault("toast_icon", None)



@st.dialog("Change Email", width="small")
def change_email_modal():
    st.write("Enter your new email address:")

    new_email = st.text_input("New email", key="modal_new_email")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel"):
            st.rerun()   # closes modal

    with col2:
        if st.button("Save", type="primary",  width="content"):
            if not new_email:
                st.warning("Please enter a valid email.")
            elif new_email == st.session_state.user.email:
                st.warning("New email must be different from the old one")
            else:
                st.session_state.user.change_email(new_email)
                st.session_state.toast_msg = "Email updated!"
                st.session_state.toast_icon = "✅"
                st.rerun()   # closes modal


@st.dialog("Change Password", width="content")
def change_password_modal(message: str = "Update Your Password"):
    st.write(message)

    old_pw = st.text_input("Current password", type="password", key="modal_old_pw")
    new_pw = st.text_input("New password", type="password", key="modal_new_pw")
    confirm_pw = st.text_input("Confirm new password", type="password", key="modal_confirm_pw")

    col1, col2 = st.columns(2)

    with col2:
        if st.button("Save", type="primary", width="content"):
            if not old_pw or not new_pw:
                st.warning("Please fill in all fields.")
            elif new_pw != confirm_pw:
                st.warning("New passwords do not match.")
            else:
                new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                if bcrypt.checkpw(new_hash.encode(), st.session_state.user.password_hash.encode()):
                    st.error("You need to change your password.")
                else:
                    st.session_state.user.change_password(new_pw)
                    st.session_state.toast_msg = "Password updated!"
                    st.session_state.toast_icon = "🔒"
                    st.rerun()
            st.rerun()

with middle:
    st.header("Account Information")
    st.space("large")
    if not st.session_state.user.password_changed:
        st.warning("You have to update your password!")
    st.text(f"User Email: {st.session_state.user.email}")
    st.text(f"User Name: {st.session_state.user.last_name}, {st.session_state.user.first_name}")
    st.text(f"Member Since: {st.session_state.user.created_at.strftime('%d %m, %Y')}")

    st.button("Change Email", on_click=change_email_modal, type="primary", width="content")
    st.button("Change Password", on_click=change_password_modal, type="primary",
              width="content")

    if st.session_state.toast_msg:
        st.toast(st.session_state.toast_msg, icon=st.session_state.toast_icon, duration="long")
        st.session_state.toast_msg = ""
        st.session_state.toast_icon = None

