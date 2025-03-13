from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict

import pyperclip
import showinfm
import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Button, Label

from datashuttle.configs import canonical_folders
from datashuttle.tui.screens import (
    get_help, modal_dialogs, new_project, project_manager, project_selector, settings
)

if TYPE_CHECKING:
    from datashuttle.tui.interface import Interface


class TuiApp(App, inherit_bindings=False):
    """
    The main app page for the DataShuttle TUI.
    """

    tui_path = Path(__file__).parent
    CSS_PATH = list(tui_path.glob("css/*.tcss"))
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Exit app", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("datashuttle", id="mainwindow_banner_label"),
            *[Button(label, id=f"mainwindow_{label.lower().replace(' ', '_')}_button")
              for label in ["Select Existing Project", "Make New Project", "Settings", "Get Help"]],
            id="mainwindow_contents_container",
        )

    def on_mount(self) -> None:
        self.set_dark_mode(self.load_global_settings().get("dark_mode", True))

    def set_dark_mode(self, dark_mode: bool) -> None:
        self.theme = "textual-dark" if dark_mode else "textual-light"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        screen_mapping = {
            "mainwindow_select_existing_project_button": project_selector.ProjectSelectorScreen,
            "mainwindow_make_new_project_button": new_project.NewProjectScreen,
            "mainwindow_settings_button": settings.SettingsScreen,
            "mainwindow_get_help_button": get_help.GetHelpScreen,
        }
        screen_class = screen_mapping.get(event.button.id)
        if screen_class:
            self.push_screen(screen_class(self), self.load_project_page if "project" in event.button.id else None)

    def load_project_page(self, interface: Interface) -> None:
        if interface:
            self.push_screen(project_manager.ProjectManagerScreen(self, interface, id="project_manager_screen"))

    def show_modal_error_dialog(self, message: str) -> None:
        self.push_screen(modal_dialogs.MessageBox(message, border_color="red"))

    def handle_open_filesystem_browser(self, path_: Path) -> None:
        if not path_.exists():
            self.show_modal_error_dialog(f"{path_.as_posix()} does not exist.")
            return
        try:
            showinfm.show_in_file_manager(path_.as_posix())
        except Exception:
            message = "Could not open file." if path_.is_file() else "Unexpected error occurred."
            self.show_modal_error_dialog(message)

    def prompt_rename_file_or_folder(self, path_: Path) -> None:
        self.push_screen(modal_dialogs.RenameFileOrFolderScreen(self, path_), lambda new_name: self.rename_file_or_folder(path_, new_name))

    def rename_file_or_folder(self, path_: Path, new_name: str) -> None:
        if not new_name:
            return
        try:
            new_path = path_.parent / (new_name if path_.is_dir() else f"{new_name}{path_.suffix}")
            os.rename(path_.as_posix(), new_path.as_posix())
            self.query_one("#project_manager_screen").update_active_tab_tree()
        except Exception as e:
            self.show_modal_error_dialog(f"Rename failed: {e}")

    def load_global_settings(self) -> Dict:
        settings_path = self.get_global_settings_path()
        if not settings_path.is_file():
            global_settings = self.get_default_global_settings()
            self.save_global_settings(global_settings)
        else:
            with open(settings_path, "r") as file:
                global_settings = yaml.safe_load(file) or {}
        return global_settings

    def get_global_settings_path(self) -> Path:
        return canonical_folders.get_datashuttle_path() / "global_tui_settings.yaml"

    def get_default_global_settings(self) -> Dict:
        return {"dark_mode": True, "show_transfer_tree_status": False}

    def save_global_settings(self, global_settings: Dict) -> None:
        settings_path = self.get_global_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w") as file:
            yaml.safe_dump(global_settings, file, sort_keys=False)

    def copy_to_clipboard(self, value: str) -> None:
        try:
            pyperclip.copy(value)
        except pyperclip.PyperclipException:
            self.show_modal_error_dialog("Clipboard copy failed (likely due to headless mode).")


def main():
    TuiApp().run()


if __name__ == "__main__":
    main()
