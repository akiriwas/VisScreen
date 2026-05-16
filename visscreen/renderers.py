class TileRenderer:
    @staticmethod
    def render_zoom(content: str, height: int = 20) -> str:
        """Standard view: shows the bottom part of the terminal (active area)."""
        lines = content.splitlines()
        return "\n".join(lines[-height:]) if lines else content

    @staticmethod
    def render_roving(content: str, height: int, width: int, offset_y: int, offset_x: int) -> str:
        """Roving Eye: Extracts a viewport slice from the terminal content."""
        lines = content.splitlines()
        if not lines:
            return ""
        
        # Ensure we have enough lines by padding if needed
        # (Though usually terminal content has many lines)
        max_y = len(lines)
        start_y = max(0, min(offset_y, max_y - height)) if max_y > height else 0
        
        viewport_lines = []
        for i in range(height):
            idx = start_y + i
            line = lines[idx] if idx < max_y else ""
            
            # Slice the line
            start_x = max(0, offset_x)
            segment = line[start_x : start_x + width]
            # Pad segment if it's shorter than width
            viewport_lines.append(segment.ljust(width))
            
        return "\n".join(viewport_lines)

    @staticmethod
    def render_minimap(content: str) -> str:
        """Minimap: Downsamples text into Braille/Block characters."""
        lines = content.splitlines()
        if not lines:
            return ""

        # A very simple 'density' minimap using Braille dots based on character presence.
        # We'll map 2x4 character blocks to one Braille character.
        # Standard terminal is ~80x24. 2x4 dots = 1 Braille char.
        # This is a complex algorithm to do perfectly; we'll start with a 
        # character-presence-based density map for the MVP.
        
        result = []
        for y in range(0, len(lines), 2):
            row_chars = []
            for x in range(0, 80, 2):
                # Check 2x2 block for characters
                # Bit mapping: 0:T-L, 1:B-L, 2:T-R, 3:B-R
                byte = 0
                if TileRenderer._has_char(lines, y, x): byte |= 0x01
                if TileRenderer._has_char(lines, y+1, x): byte |= 0x02
                if TileRenderer._has_char(lines, y, x+1): byte |= 0x04
                if TileRenderer._has_char(lines, y+1, x+1): byte |= 0x08
                
                # Map 4 bits to a block character (16 combinations)
                blocks = " ▘▖▌▝▀▞▛▗▚▄▙▐▜▟█"
                row_chars.append(blocks[byte])
            result.append("".join(row_chars))
            
        return "\n".join(result)

    @staticmethod
    def _has_char(lines, y, x):
        try:
            return len(lines[y][x].strip()) > 0
        except IndexError:
            return False
