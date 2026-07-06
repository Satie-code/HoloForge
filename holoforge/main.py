import sys
import os

# Add workspace root to path when running as a script so package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from holoforge.core.app import HoloForgeApp
except ImportError as err:
    # provide a user-friendly hint rather than a raw traceback
    print("Failed to import HoloForge. Make sure you're running the script from the repository root and that all "
          "dependencies are installed (see Requirement.md).")
    print("Error:", err)
    raise

if __name__ == "__main__":
    app = HoloForgeApp()
    app.run()
