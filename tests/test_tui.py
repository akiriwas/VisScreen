import unittest
import pytest
from textual.widgets import Static
from visscreen.app import SessionTile, VisScreenApp
from visscreen.manager import ScreenManager
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_session_tile_rendering():
    app = VisScreenApp()
    async with app.run_test() as pilot:
        tile = SessionTile("1234", "test_session", "Detached", "12:00")
        await app.query_one("#grid-view").mount(tile)
        
        info_bar = tile.query_one("#info-bar", Static)
        assert "1234.test_session" in str(info_bar.renderable)
        assert "Detached" in str(info_bar.renderable)
        assert "12:00" in str(info_bar.renderable)

@pytest.mark.asyncio
async def test_view_toggle():
    app = VisScreenApp()
    async with app.run_test() as pilot:
        list_view = app.query_one("#list-view")
        grid_view = app.query_one("#grid-view")
        
        assert list_view.display == "block"
        assert grid_view.display == "none"
        
        await pilot.press("v")
        assert list_view.display == "none"
        assert grid_view.display == "block"
        
        await pilot.press("v")
        assert list_view.display == "block"
        assert grid_view.display == "none"
