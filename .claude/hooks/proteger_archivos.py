from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
from guardian import main
sys.exit(main("protect", ".claude"))
