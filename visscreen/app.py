from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Input, Static, Label, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual.screen import ModalScreen
from .manager import ScreenManager

class NewSessionModal(ModalScreen[str]):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Enter new session name:"),
            Input(placeholder="session_name", id="session-name"),
            Horizontal(
                Button("Create", variant="primary", id="create"),
                Button("Cancel", variant="error", id="cancel"),
            ),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            name = self.query_one("#session-name").value
            self.dismiss(name)
        else:
            self.dismiss(None)

class KillConfirmModal(ModalScreen[bool]):
    def __init__(self, session_id: str, session_name: str):
        super().__init__()
        self.session_id = session_id
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Are you sure you want to kill session {self.session_id}.{self.session_name}?"),
            Horizontal(
                Button("Kill", variant="error", id="kill"),
                Button("Cancel", variant="primary", id="cancel"),
            ),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kill":
            self.dismiss(True)
        else:
            self.dismiss(False)

class VisScreenApp(App):
    TITLE = "VisScreen"
    SUB_TITLE = "Manage GNU Screen Sessions"
    CSS = """
    #main-container {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
        width: 70%;
        border: solid green;
    }
    #detail-pane {
        width: 30%;
        border: solid blue;
        padding: 1;
    }
    #search-container {
        height: auto;
        margin: 1;
    }
    #dialog {
        padding: 1 2;
        background: $panel;
        border: thick $primary;
        width: 40;
        height: auto;
        align: center middle;
    }
    #dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    #dialog Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "rejoin", "Rejoin", show=False),
        Binding("d", "detach_rejoin", "Detach & Rejoin", show=True),
        Binding("n", "new_session", "New Session", show=True),
        Binding("k", "kill_session", "Kill Session", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Container(
                Input(placeholder="Search sessions...", id="search-input"),
                id="search-container"
            ),
            Horizontal(
                DataTable(id="sessions-table"),
                Static(id="detail-pane"),
                id="main-container"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Time", "State")
        table.cursor_type = "row"
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        table = self.query_one(DataTable)
        search_value = self.query_one("#search-input").value.lower()
        table.clear()
        
        self.sessions = ScreenManager.list_sessions()
        for s in self.sessions:
            if search_value in s.name.lower() or search_value in s.id.lower():
                table.add_row(s.id, s.name, s.time, s.state, key=s.id)
        
        if not table.rows:
            self.query_one("#detail-pane").update("No sessions found.")
        else:
            self.update_detail_pane()

    def update_detail_pane(self) -> None:
        table = self.query_one(DataTable)
        pane = self.query_one("#detail-pane")
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            session = next((s for s in self.sessions if s.id == row_key.value), None)
            if session:
                pane.update(f"[bold]Session Details[/bold]\n\n"
                            f"ID: {session.id}\n"
                            f"Name: {session.name}\n"
                            f"Time: {session.time}\n"
                            f"State: {session.state}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_rejoin()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.update_detail_pane()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.refresh_sessions()

    def action_refresh(self) -> None:
        self.refresh_sessions()

    def action_rejoin(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            session_id = row_key.value
            self.exit()
            ScreenManager.rejoin(session_id)

    def action_detach_rejoin(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            session_id = row_key.value
            self.exit()
            ScreenManager.rejoin(session_id, detach=True)

    def action_kill_session(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            session_id = row_key.value
            session_name = next((s.name for s in self.sessions if s.id == session_id), "")
            
            def check_kill(should_kill: bool) -> None:
                if should_kill:
                    ScreenManager.kill(session_id)
                    self.refresh_sessions()
            
            self.push_screen(KillConfirmModal(session_id, session_name), check_kill)

    def action_new_session(self) -> None:
        def create_new(name: str | None) -> None:
            if name is not None:
                self.exit()
                ScreenManager.create(name if name.strip() else None)
        
        self.push_screen(NewSessionModal(), create_new)

def run():
    app = VisScreenApp()
    app.run()

if __name__ == "__main__":
    run()
