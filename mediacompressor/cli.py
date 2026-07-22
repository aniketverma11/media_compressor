"""
Command-Line Interface entry point for pip-installed package.
Runs when user executes: mediacompressor or media-compressor
"""

import sys
from mediacompressor.ui.main_window import MainWindow

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Fatal error launching MediaCompressor: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
