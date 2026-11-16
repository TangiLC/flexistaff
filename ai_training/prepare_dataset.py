"""Prépare le dataset YOLO à partir de l'export CVAT (étape 5.3 du guide).

Entrée : l'archive (ou le dossier décompressé) exportée depuis CVAT au format
« Ultralytics YOLO Detection 1.0 ». CVAT range souvent toutes les images dans
un seul sous-ensemble (images/train ou images/default) : ce script les
redécoupe en train / val (80 / 20 par défaut, tirage reproductible).

Sortie :
    dataset/
    ├── data.yaml
    ├── images/{train,val}/
    └── labels/{train,val}/

Les noms de classes sont repris du data.yaml de l'export, dans l'ordre CVAT.
Une image sans fichier de label (aucune boîte) est conservée avec un label
vide : c'est un exemple négatif, utile au modèle.

Usage :
    python prepare_dataset.py export_cvat.zip --out dataset --val 0.2 --seed 42
"""

from __future__ import annotations

import argparse
import random
import shutil
import tempfile
import zipfile
from pathlib import Path

import yaml

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def _find_root(base: Path) -> Path:
    """Dossier qui contient data.yaml (l'archive peut avoir un niveau en plus)."""
    candidates = sorted(base.rglob("data.yaml"), key=lambda p: len(p.parts))
    if not candidates:
        raise FileNotFoundError(f"Aucun data.yaml dans {base} : est-ce bien un export Ultralytics YOLO ?")
    return candidates[0].parent


def _read_names(data_yaml: Path) -> dict[int, str]:
    cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    names = cfg.get("names")
    if isinstance(names, list):
        names = dict(enumerate(names))
    if not names:
        raise ValueError(f"Pas de clé 'names' dans {data_yaml}")
    return {int(k): str(v) for k, v in names.items()}


def _pairs(root: Path) -> list[tuple[Path, Path | None]]:
    """Associe chaque image à son label : images/<x>/a.jpg -> labels/<x>/a.txt."""
    images_dir = root / "images"
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Pas de dossier images/ dans {root}")
    pairs = []
    for img in sorted(images_dir.rglob("*")):
        if img.suffix.lower() not in IMG_EXT:
            continue
        rel = img.relative_to(images_dir).with_suffix(".txt")
        lbl = root / "labels" / rel
        pairs.append((img, lbl if lbl.exists() else None))
    return pairs


def _class_counts(pairs, names) -> dict[str, int]:
    counts = {n: 0 for n in names.values()}
    for _, lbl in pairs:
        if lbl is None:
            continue
        for line in lbl.read_text().splitlines():
            if line.strip():
                cls = int(line.split()[0])
                key = names.get(cls, f"?{cls}")  # index inconnu : signalé plutôt qu'ignoré
                counts[key] = counts.get(key, 0) + 1
    return counts


def prepare(export: str | Path, out: str | Path, val_ratio: float = 0.2, seed: int = 42) -> Path:
    export, out = Path(export), Path(out)
    with tempfile.TemporaryDirectory() as tmp:
        if export.is_file() and zipfile.is_zipfile(export):
            with zipfile.ZipFile(export) as zf:
                zf.extractall(tmp)
            base = Path(tmp)
        elif export.is_dir():
            base = export
        else:
            raise FileNotFoundError(f"{export} n'est ni une archive .zip ni un dossier")

        root = _find_root(base)
        names = _read_names(root / "data.yaml")
        pairs = _pairs(root)
        if len(pairs) < 2:
            raise ValueError(f"Seulement {len(pairs)} image(s) trouvée(s) : impossible de découper")

        # Noms de fichiers uniques (deux jobs peuvent contenir le même nom d'image)
        seen: set[str] = set()
        for img, _ in pairs:
            if img.name in seen:
                raise ValueError(f"Nom d'image en double : {img.name}")
            seen.add(img.name)

        rng = random.Random(seed)
        rng.shuffle(pairs)
        n_val = max(1, round(len(pairs) * val_ratio))
        splits = {"val": pairs[:n_val], "train": pairs[n_val:]}

        if out.exists():
            shutil.rmtree(out)
        for split, items in splits.items():
            (out / "images" / split).mkdir(parents=True)
            (out / "labels" / split).mkdir(parents=True)
            for img, lbl in items:
                shutil.copy2(img, out / "images" / split / img.name)
                dst = out / "labels" / split / (img.stem + ".txt")
                if lbl is not None:
                    shutil.copy2(lbl, dst)
                else:
                    dst.touch()

        data = {
            "path": str(out.resolve()),
            "train": "images/train",
            "val": "images/val",
            "nc": len(names),
            "names": dict(sorted(names.items())),
        }
        (out / "data.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        print(f"{len(splits['train'])} images en train, {len(splits['val'])} en val -> {out}")
        print(f"{sum(1 for _, l in pairs if l is None)} image(s) sans boîte (exemples négatifs)")
        for split, items in splits.items():
            print(f"  boîtes par classe ({split}) :", _class_counts(items, names))
        return out / "data.yaml"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("export", type=Path, help="archive .zip ou dossier exporté depuis CVAT")
    p.add_argument("--out", type=Path, default=Path("dataset"))
    p.add_argument("--val", type=float, default=0.2, help="part des images en validation (défaut 0.2)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    prepare(args.export, args.out, args.val, args.seed)


if __name__ == "__main__":
    main()
