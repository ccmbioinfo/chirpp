import streamlit as st
import bcrypt


st.session_state.force_password_change=(not st.session_state.user.password_changed)


st.header("You must change your password before you can use this page.")
st.markdown('</div>', unsafe_allow_html=True)

left, middle, right = st.columns([1, 10, 1])

with middle:
    old_pw = st.text_input("Current password", type="password", key="modal_old_pw")
    new_pw = st.text_input("New password", type="password", key="modal_new_pw")
    confirm_pw = st.text_input("Confirm new password", type="password", key="modal_confirm_pw")

    col1, col2 = st.columns(2)

    with col2:
        if st.button("Save", type="primary", width="content"):
            if not old_pw or not new_pw:
                st.error("Please fill in all fields.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
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