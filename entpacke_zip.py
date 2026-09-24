from pathlib import Path
from zipfile import ZipFile


ZIP_DATEI = Path(__file__).with_name("42.zip")
ZIEL_ORDNER = ZIP_DATEI.with_suffix("")


def ist_sicherer_pfad(ziel: Path, basis: Path) -> bool:
    try:
        ziel.resolve().relative_to(basis.resolve())
        return True
    except ValueError:
        return False


def entpacke_zip() -> None:
    if not ZIP_DATEI.is_file():
        raise FileNotFoundError(f"ZIP-Datei nicht gefunden: {ZIP_DATEI}")

    ZIEL_ORDNER.mkdir(exist_ok=True)

    with ZipFile(ZIP_DATEI) as archiv:
        for eintrag in archiv.infolist():
            ziel = ZIEL_ORDNER / eintrag.filename
            if not ist_sicherer_pfad(ziel, ZIEL_ORDNER):
                raise ValueError(f"Unsicherer Pfad im ZIP-Archiv: {eintrag.filename}")

        archiv.extractall(ZIEL_ORDNER)

    print(f"Entpackt nach: {ZIEL_ORDNER}")


if __name__ == "__main__":
    entpacke_zip()
