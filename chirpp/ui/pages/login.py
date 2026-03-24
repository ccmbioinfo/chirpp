import base64
from pathlib import Path

from chirpp_ui.utils.classes import *

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")


root_dir = Path(__file__).parent.parent
img_path = root_dir /"assets" / "login_background.jpg"
st.set_page_config(page_icon=root_dir/ "assets" / "favicon.ico")

def get_base64_img(path):
    if path.is_file():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


img_b64 = get_base64_img(img_path)

# Injected Styling
if img_b64:
    st.markdown(f"""
        <style>
        /* Remove Streamlit default margins */
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
        header, footer {{ visibility: hidden; }}

        /* The main split container */
        .login-frame {{
            display: flex;
            width: 100vw;
            height: 100vh;
            position: fixed;
            top: 0;
            left: 0;
        }}

        .login-img {{
            flex: 2;
            background-image: url("data:image/jpeg;base64,{img_b64}");
            background-size: cover;
            background-position: center;
        }}

        .login-form-area {{
            flex: 1;
            background-color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0 0%;
        }}
        </style>

        <div class="login-frame">
            <div class="login-img"></div>
            <div class="login-form-area"></div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at: {img_path}")

left_space, right_form = st.columns([3, 1])

with right_form:
    # Adding vertical padding to center the form in the white section
    for _ in range(15): st.write("")
    content, right_sp = st.columns([16, 3])
    with content:
        with st.container():
            with st.form("login_form", border=False):
                st.title("CHIRPP Login")
                st.write("Welcome back! Please enter your details.")

                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", placeholder="Enter your password", type="password")

                st.write("")  # Spacer

                # This button captures the "Enter" key automatically
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)

                if submit:
                    if email and password:
                        new_user = User.from_db(email, password, st.session_state.database)
                        if new_user is not None:
                            st.session_state.user = new_user
                            st.rerun()
                        else:
                            st.error("Invalid email or password. \n\n"
                                     "If you forgot your password, please email your CHIRPP manager.")
                    else:
                        st.warning("Please fill in all fields.")

            st.markdown("---")
            st.caption("SickKids CHIRPP Platform © 2026")