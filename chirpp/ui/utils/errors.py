import streamlit as st

def toast_exception(cls):
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Show a toast whenever the exception is constructed
        st.toast(f"{cls.__name__}: {self}", icon="❌")
    cls.__init__ = new_init

    def raise_or_toast(self):
        st.toast(f"{cls.__name__}: {self}", icon="❌")
    cls.throw = raise_or_toast  # You call e.throw() instead of raise e
    return cls

@toast_exception
class NoUserError(Exception):
    pass

@toast_exception
class TooManyUsersError(Exception):
    pass

@toast_exception
class DbConnectionError(Exception):
    pass

@toast_exception
class RoleError(Exception):
    pass