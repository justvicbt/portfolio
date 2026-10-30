"""Point d'entrée : python -m f1cc <commande>

  etl   télécharge les courses (OpenF1), transforme et reconstruit la base data/f1cc.db
  app   lance le tableau de bord Streamlit (équivaut à streamlit run src/f1cc/app.py)
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m f1cc", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["etl", "app"])
    args = parser.parse_args()
    if args.command == "etl":
        from . import etl
        etl.main()
    else:
        app = Path(__file__).with_name("app.py")
        sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)]))


if __name__ == "__main__":
    main()
