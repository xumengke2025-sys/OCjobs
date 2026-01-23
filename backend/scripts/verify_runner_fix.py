
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

try:
    from app.services.simulation_runner import SimulationRunner
    print("Successfully imported SimulationRunner")
    
    import platform
    print(f"Platform: {platform.system()}")
    
    # Check if stop_simulation has the new logic (by inspecting source or just relying on import)
    # We can't easily inspect the source at runtime for specific lines without reading file, 
    # but successful import means syntax is correct.
    
except Exception as e:
    print(f"Failed to import: {e}")
    import traceback
    traceback.print_exc()
