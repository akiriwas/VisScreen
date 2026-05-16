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

class SessionTile(Vertical):
    can_focus = True

    def __init__(self, session_id: str, session_name: str, state: str, time: str, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.session_name = session_name
        self.state = state
        self.time = time

    def compose(self) -> ComposeResult:
        yield Static(id="info-bar")
        yield Static(id="snapshot-text")

    def on_mount(self) -> None:
        self.update_snapshot()

    def update_snapshot(self) -> None:
        content = ScreenManager.get_session_snapshot(self.session_id)
        # Truncate to ensure it fits well in the tile
        lines = content.splitlines()[:20]
        self.query_one("#snapshot-text").update("\n".join(lines))
        self.query_one("#info-bar").update(
            f"[bold] {self.session_id}.{self.session_name} [/bold] | {self.state} | {self.time}"
        )

class VisScreenApp(App):
    TITLE = "VisScreen"
    SUB_TITLE = "Manage GNU Screen Sessions"
    CSS = """
    #main-container {
        height: 1fr;
    }
    #list-view {
        height: 1fr;
    }
    #grid-view {
        height: 1fr;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        display: none;
        overflow-y: scroll;
        padding: 1;
    }
    SessionTile {
        border: solid yellow;
        height: 28;
        padding: 0;
        margin: 1;
    }
    SessionTile:focus {
        border: double green;
    }
    SessionTile:focus #info-bar {
        background: $accent;
        color: $text-primary;
    }
    #info-bar {
        height: 3;
        background: $primary;
        color: $text;
        padding: 0 1;
        content-align: center middle;
        width: 100%;
    }
    #snapshot-text {
        height: 23;
        padding: 1;
        overflow-y: hidden;
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
        Binding("v", "toggle_view", "Toggle View"),
        Binding("up", "move_focus_up", "Move Up", show=False),
        Binding("down", "move_focus_down", "Move Down", show=False),
        Binding("left", "move_focus_left", "Move Left", show=False),
        Binding("right", "move_focus_right", "Move Right", show=False),
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
            Container(
                Horizontal(
                    DataTable(id="sessions-table"),
                    Static(id="detail-pane"),
                    id="list-view"
                ),
                Container(id="grid-view"),
                id="main-container"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Time", "State")
        table.cursor_type = "row"
        self.refresh_sessions()
        self.set_interval(5.0, self.refresh_snapshots)

    def refresh_sessions(self) -> None:
        table = self.query_one(DataTable)
        search_value = self.query_one("#search-input").value.lower()
        table.clear()
        
        self.sessions = ScreenManager.list_sessions()
        
        # Update List View
        for s in self.sessions:
            if search_value in s.name.lower() or search_value in s.id.lower():
                table.add_row(s.id, s.name, s.time, s.state, key=s.id)
        
        if not table.rows:
            self.query_one("#detail-pane").update("No sessions found.")
        else:
            self.update_detail_pane()

        # Update Grid View structure
        grid = self.query_one("#grid-view")
        grid.remove_children()
        for s in self.sessions:
            if search_value in s.name.lower() or search_value in s.id.lower():
                grid.mount(SessionTile(s.id, s.name, s.state, s.time))

    def refresh_snapshots(self) -> None:
        # Only poll snapshots if Grid View is visible
        grid = self.query_one("#grid-view")
        if grid.display:
            for tile in grid.query(SessionTile):
                tile.update_snapshot()

    def action_toggle_view(self) -> None:
        list_view = self.query_one("#list-view")
        grid_view = self.query_one("#grid-view")
        
        if not list_view.display:
            # Switch to List View
            list_view.display = True
            grid_view.display = False
            self.query_one(DataTable).focus()
        else:
            # Switch to Grid View
            list_view.display = False
            grid_view.display = True
            # Focus the first tile if available
            tiles = list(grid_view.query(SessionTile))
            if tiles:
                tiles[0].focus()
            else:
                grid_view.focus()
            self.refresh_snapshots() # Immediate update when switching to grid

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

    def move_grid_focus(self, delta: int) -> None:
        grid = self.query_one("#grid-view")
        tiles = list(grid.query(SessionTile))
        if not tiles:
            return
        
        current_index = -1
        if isinstance(self.focused, SessionTile):
            try:
                current_index = tiles.index(self.focused)
            except ValueError:
                pass
        elif self.focused is None or self.focused == grid:
            # If nothing focused in grid, start at first tile
            tiles[0].focus()
            return
            
        new_index = max(0, min(len(tiles) - 1, current_index + delta))
        tiles[new_index].focus()

    def action_refresh(self) -> None:
        self.refresh_sessions()

    def action_move_focus_up(self) -> None:
        if not self.query_one("#list-view").display:
            self.move_grid_focus(-2)

    def action_move_focus_down(self) -> None:
        if not self.query_one("#list-view").display:
            self.move_grid_focus(2)

    def action_move_focus_left(self) -> None:
        if not self.query_one("#list-view").display:
            self.move_grid_focus(-1)

    def action_move_focus_right(self) -> None:
        if not self.query_one("#list-view").display:
            self.move_grid_focus(1)

    def action_rejoin(self) -> None:
        session_id = self.get_active_session_id()
        if session_id:
            self.exit()
            ScreenManager.rejoin(session_id)

    def action_detach_rejoin(self) -> None:
        session_id = self.get_active_session_id()
        if session_id:
            self.exit()
            ScreenManager.rejoin(session_id, detach=True)

    def action_kill_session(self) -> None:
        session_id = self.get_active_session_id()
        if session_id:
            session_name = next((s.name for s in self.sessions if s.id == session_id), "")
            
            def check_kill(should_kill: bool) -> None:
                if should_kill:
                    ScreenManager.kill(session_id)
                    self.refresh_sessions()
            
            self.push_screen(KillConfirmModal(session_id, session_name), check_kill)

    def get_active_session_id(self) -> str | None:
        list_view = self.query_one("#list-view")
        if list_view.display:
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                return str(row_key.value)
        else:
            focused = self.focused
            if isinstance(focused, SessionTile):
                return focused.session_id
        return None

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
