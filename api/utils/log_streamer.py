import asyncio
from typing import Optional


# Async generator to yield log lines
async def log_streamer(file_path: str, lines: Optional[int] = None):
    
    new_lines = []

    with open(file_path, "r") as f:
        # Read the entire file first and reverse the order of lines
        all_lines = f.readlines()

        # Show only 100 lines if `lines` is None
        if lines is None:
            all_lines = all_lines[-100:]
        
        # If `lines` parameter is provided, limit the number of lines to show
        if lines is not None and lines < len(all_lines):
            all_lines = all_lines[-lines:]  # Get the last `lines` lines

        # # Yield the initial lines in reverse order (newest at the top)
        for line in reversed(all_lines):
            yield line

        # # Continue streaming new lines appended to the file
        while True:
            line = f.readline()
            if line:
                # Add new lines to the beginning of the list
                new_lines.append(line)
                # Yield new lines in reverse order to show newest at the top
                for new_line in reversed(new_lines):
                    yield new_line
                new_lines = []  # Clear after yielding
            else:
                # If no new lines, sleep for a short time before checking again
                await asyncio.sleep(0.1)
