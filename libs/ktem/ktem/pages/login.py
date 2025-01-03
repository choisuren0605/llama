import hashlib

import gradio as gr
from ktem.app import BasePage
from ktem.db.models import User, engine
from sqlmodel import Session, select

fetch_creds = """
function() {
    const username = getStorage('username', '')
    const password = getStorage('password', '')
    return [username, password, null];
}
"""

signin_js = """
function(usn, pwd) {
    setStorage('username', usn);
    setStorage('password', pwd);
    return [usn, pwd];
}
"""

class LoginPage(BasePage):
    public_events = ["onSignIn"]

    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        gr.Markdown(f"# Welcome to {self._app.app_name}!")

        with gr.Tabs() as tabs:
            with gr.Tab(label="Login"):
                self.usn = gr.Textbox(label="Username", visible=True)
                self.pwd = gr.Textbox(label="Password", type="password", visible=True)
                self.btn_login = gr.Button("Login", visible=True)

            with gr.Tab(label="Sign Up"):
                self.usn_new = gr.Textbox(label="Username", interactive=True)
                self.pwd_new = gr.Textbox(
                    label="Password", type="password", interactive=True
                )
                self.pwd_cnf_new = gr.Textbox(
                    label="Confirm Password", type="password", interactive=True
                )
                self.btn_signup = gr.Button("Sign Up", visible=True)

    def on_register_events(self):
        # Login Event
        onSignIn = gr.on(
            triggers=[self.btn_login.click, self.pwd.submit],
            fn=self.login,
            inputs=[self.usn, self.pwd],
            outputs=[self._app.user_id, self.usn, self.pwd],
            show_progress="hidden",
            js=signin_js,
        ).then(
            self.toggle_login_visibility,
            inputs=[self._app.user_id],
            outputs=[self.usn, self.pwd, self.btn_login],
        )
        for event in self._app.get_event("onSignIn"):
            onSignIn = onSignIn.success(**event)

        # Sign-Up Event
        self.btn_signup.click(
            self.create_user,
            inputs=[self.usn_new, self.pwd_new, self.pwd_cnf_new],
            outputs=[self.usn_new, self.pwd_new, self.pwd_cnf_new],
        )

    def toggle_login_visibility(self, user_id):
        return (
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
        )

    def create_user(self, usn, pwd, pwd_cnf):
        errors = self.validate_user_input(usn, pwd, pwd_cnf)
        if errors:
            gr.Warning(errors)
            return usn, pwd, pwd_cnf

        hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
        with Session(engine) as session:
            statement = select(User).where(User.username_lower == usn.lower())
            result = session.exec(statement).all()
            if result:
                gr.Warning(f'Username "{usn}" already exists')
                return usn, pwd, pwd_cnf

            user = User(
                username=usn, username_lower=usn.lower(), password=hashed_password
            )
            session.add(user)
            session.commit()
            gr.Info(f'User "{usn}" created successfully')

        return "", "", ""

    def login(self, usn, pwd):
        if not usn or not pwd:
            return None, usn, pwd

        hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
        with Session(engine) as session:
            stmt = select(User).where(
                User.username_lower == usn.lower().strip(),
                User.password == hashed_password,
            )
            result = session.exec(stmt).all()
            if result:
                return result[0].id, "", ""

            gr.Warning("Invalid username or password")
            return None, usn, pwd

    def validate_user_input(self, usn, pwd, pwd_cnf):
        errors = []
        if len(usn) < 3:
            errors.append("Username must be at least 3 characters long")
        if len(usn) > 32:
            errors.append("Username must be at most 32 characters long")
        if not usn.replace("_", "").isalnum():
            errors.append("Username must contain only alphanumeric characters and underscores")
        if pwd != pwd_cnf:
            errors.append("Passwords do not match")
        if len(pwd) < 8:
            errors.append("Password must be at least 8 characters long")
        return "; ".join(errors)
