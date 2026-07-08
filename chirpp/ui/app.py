import os

import streamlit as st
from dotenv import dotenv_values
from chirpp.ui.utils.classes import *

secrets=dotenv_values(os.environ["SECRETS_FILE"])
st.session_state.database=Database(user=secrets["USER"],pwd=secrets["PASSWORD"], db_name=secrets["DB_NAME"],
                   host=secrets["HOST"], port=secrets["PORT"])

if "user" not in st.session_state:
    st.session_state.user = None

st.set_page_config(page_title="SickKids CHIRPP Platform",
                   layout="wide")

#there needs to be a full page for just changing password and that's it
login_page = st.Page("pages/login.py", title="Login")
admin = st.Page("pages/admin.py", title="Admin")
change_password=st.Page("pages/change_password.py", title="First Login")
account = st.Page("pages/account.py", title="Account")
report = st.Page("pages/report.py", title="CHIRPP Report")
search = st.Page("pages/search.py", title="Search")


if st.session_state.user is None:
    pg = st.navigation([login_page])
else:
    if not st.session_state.user.password_changed:
        pages=[account]
    else:
        pages= [report, search, account]
    if st.session_state.user.is_manager:
        pages.append(admin)
    pg = st.navigation(pages)

    st.markdown(
        """
        <style>
            /* 1. This identifies the sidebar container */
            section[data-testid="stSidebar"] {
                display: flex;
                flex-direction: column;
            }

            /* 2. This targets the bottom container specifically */
            div[data-testid="stVerticalBlock"] > div:last-child.st-emotion-cache-mq02tm {
                margin-top: auto;
            }

            /* 3. The most reliable way: Pin a div to the bottom of the sidebar */
            .fixed-logout {
                position: fixed;
                bottom: 0;
                width: 336px; /* Default Streamlit sidebar width */
                background-color: white;
                padding: 1rem;
                border-top: 1px solid rgba(49, 51, 63, 0.2);
                z-index: 1000;
            }

            /* Adjust for dark mode */
            @media (prefers-color-scheme: dark) {
                .fixed-logout {
                    background-color: #0e1117;
                    border-top: 1px solid #31333f;
                }
            }

            /* Ensure the navigation menu doesn't get cut off by the fixed footer */
            [data-testid="stSidebarNav"] {
                margin-bottom: 80px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        # Wrap the button in a div that our CSS can "pin"
        st.markdown('<div class="fixed-logout">', unsafe_allow_html=True)
        st.caption(f"Logged in as: **{st.session_state.user.email}**")
        if st.button("Logout", use_container_width=True, type="primary"):
            st.session_state.user = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


pg.run()