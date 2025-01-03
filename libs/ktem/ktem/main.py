import gradio as gr
from decouple import config
from ktem.app import BaseApp
from ktem.pages.chat import ChatPage
from ktem.pages.resources import ResourcesTab
from ktem.pages.settings import SettingsPage
from ktem.pages.setup import SetupPage
from theflow.settings import settings as flowsettings
from ktem.db.engine import engine
from ktem.db.models import User
from sqlmodel import Session, select

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False

def toggle_first_setup_visibility():
    global KH_APP_DATA_EXISTS
    is_first_setup = KH_DEMO_MODE or not KH_APP_DATA_EXISTS
    KH_APP_DATA_EXISTS = True
    return gr.update(visible=is_first_setup), gr.update(visible=not is_first_setup)

class App(BaseApp):
    def ui(self):
        self._tabs = {}
        
        with gr.Tabs() as self.tabs:
            # Login Tab
            if self.f_user_management:
                from ktem.pages.login import LoginPage
                with gr.Tab("Welcome", elem_id="login-tab", id="login-tab") as self._tabs["login-tab"]:
                    self.login_page = LoginPage(self)

            # Chat Tab
            with gr.Tab("Chat", elem_id="chat-tab", id="chat-tab", 
                       visible=not self.f_user_management) as self._tabs["chat-tab"]:
                self.chat_page = ChatPage(self)

            # Handle indices tabs based on count
            if self.index_manager.indices:
                if len(self.index_manager.indices) == 1:
                    index = self.index_manager.indices[0]
                    with gr.Tab(f"{index.name}", elem_id=f"index-{index.id}-tab",
                              elem_classes=["fill-main-area-height", "scrollable"],
                              id=f"index-{index.id}-tab",
                              visible=False) as self._tabs[f"index-{index.id}-tab"]:
                        page = index.get_index_page_ui()
                        setattr(self, f"_index_{index.id}", page)
                else:
                    with gr.Tab("Files", elem_id="indices-tab",
                              elem_classes=["fill-main-area-height", "scrollable"],
                              id="indices-tab",
                              visible=False) as self._tabs["indices-tab"]:
                        for index in self.index_manager.indices:
                            with gr.Tab(f"{index.name} Collection",
                                      elem_id=f"index-{index.id}-tab") as self._tabs[f"index-{index.id}-tab"]:
                                page = index.get_index_page_ui()
                                setattr(self, f"_index_{index.id}", page)

            # Resources Tab
            with gr.Tab("Resources", elem_id="resources-tab", id="resources-tab",
                       visible=False,
                       elem_classes=["fill-main-area-height", "scrollable"]) as self._tabs["resources-tab"]:
                self.resources_page = ResourcesTab(self)

            # Settings Tab
            with gr.Tab("Settings", elem_id="settings-tab", id="settings-tab",
                       visible=not self.f_user_management,
                       elem_classes=["fill-main-area-height", "scrollable"]) as self._tabs["settings-tab"]:
                self.settings_page = SettingsPage(self)

        if KH_ENABLE_FIRST_SETUP:
            with gr.Column(visible=False) as self.setup_page_wrapper:
                self.setup_page = SetupPage(self)

    def on_subscribe_public_events(self):
        if self.f_user_management:
            def toggle_login_visibility(user_id):
                if not user_id:
                    # Not logged in - show only login tab
                    return [
                        gr.update(visible=(k == "login-tab"))
                        for k in self._tabs.keys()
                    ] + [gr.update(selected="login-tab")]

                with Session(engine) as session:
                    user = session.exec(
                        select(User).where(User.id == user_id)
                    ).first()

                    if not user:
                        return [
                            gr.update(visible=(k == "login-tab"))
                            for k in self._tabs.keys()
                        ] + [gr.update(selected="login-tab")]

                    is_admin = user.admin

                # Update visibility for all tabs
                updates = []
                for tab_key in self._tabs.keys():
                    # Default visibility is False
                    visible = False
                    
                    # Login tab is hidden after login
                    if tab_key == "login-tab":
                        visible = False
                    # Admin-only tabs
                    elif tab_key in ["resources-tab", "indices-tab"] or tab_key.startswith("index-"):
                        visible = is_admin
                    # Regular tabs visible to all logged-in users
                    else:
                        visible = True
                        
                    updates.append(gr.update(visible=visible))

                # Add tab selection update (default to chat)
                updates.append(gr.update(selected="chat-tab"))
                return updates

            # Sign In Event
            self.subscribe_event(
                name="onSignIn",
                definition={
                    "fn": toggle_login_visibility,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()) + [self.tabs],
                    "show_progress": "hidden",
                },
            )

            # Sign Out Event
            self.subscribe_event(
                name="onSignOut",
                definition={
                    "fn": toggle_login_visibility,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()) + [self.tabs],
                    "show_progress": "hidden",
                },
            )

        if KH_ENABLE_FIRST_SETUP:
            self.subscribe_event(
                name="onFirstSetupComplete",
                definition={
                    "fn": toggle_first_setup_visibility,
                    "inputs": [],
                    "outputs": [self.setup_page_wrapper, self.tabs],
                    "show_progress": "hidden",
                },
            )

    def _on_app_created(self):
        if KH_ENABLE_FIRST_SETUP:
            self.app.load(
                toggle_first_setup_visibility,
                inputs=[],
                outputs=[self.setup_page_wrapper, self.tabs],
            )