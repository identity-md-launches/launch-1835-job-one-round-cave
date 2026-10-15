"""Check the current gathering output contract without network access."""
import hashlib
import json
from pathlib import Path
import subprocess

from check_delivery_19 import Gallery, ROOT, jpeg_info, png_info

BARE = "https://api.imd.fun/artifacts/ce5dbc18003365f5a1bf9014a2a357c2cb5c5dc2335dd0eb9b661ae703d36308"


def main():
    wall = ROOT / "artifacts/gathering/wall-v21.png"
    preview = ROOT / "dist/gathering/21.jpg"
    digest = hashlib.sha256(wall.read_bytes()).hexdigest()
    assert png_info(wall) == {"format": "PNG", "width": 1254, "height": 1254, "mode": "RGB"}
    assert jpeg_info(preview) == {"format": "JPEG", "width": 512, "height": 512}
    assert preview.stat().st_size <= 100_000
    record = json.loads((ROOT / "dist/gathering/21.json").read_text())
    assert set(record) == {"name", "image", "attributes"}
    assert record["image"] == "https://api.imd.fun/artifacts/" + digest
    assert [a["trait_type"] for a in record["attributes"]] == [
        "Cave", "Wall", "Number", "Left behind", "Meaning", "One thing"]
    assert all(set(a) == {"trait_type", "value"} for a in record["attributes"])
    assert [a["value"] for a in record["attributes"]] == [
        "Water", "Gathering", 21, "Pinned RPC batch coverage review",
        "Four ochre seed pods share one charcoal twig, each branch checked before the harvest.",
        "Gathering"]

    folders = [f"line-{n}" for n in range(1, 5)] + ["gathering"]
    links, images = [], []
    painted_count = pending_count = 0
    for folder in folders:
        directory = ROOT / "dist" / folder
        records = [(p, json.loads(p.read_text())) for p in directory.glob("[0-9][0-9].json")]
        records.sort(key=lambda item: int(item[0].stem), reverse=True)
        painted = [(p, r) for p, r in records if r["name"] != "Not painted yet"]
        pending = [(p, r) for p, r in records if r["name"] == "Not painted yet"]
        painted_count += len(painted)
        pending_count += len(pending)
        assert all((directory / f"{n:02}.json").is_file() for n in range(1, 22))
        for path, item in painted + pending:
            links.append(path.relative_to(ROOT / "dist").as_posix())
            assert set(item) == {"name", "image", "attributes"}
            if item["name"] == "Not painted yet":
                assert item == {"name": "Not painted yet", "image": BARE,
                                "attributes": [{"trait_type": "Cave", "value": "Water"}]}
                assert not path.with_suffix(".jpg").exists()
                images.append(BARE)
            else:
                attrs = {a["trait_type"]: a["value"] for a in item["attributes"]}
                assert list(attrs) == ["Cave", "Wall", "Number", "Left behind", "Meaning", "One thing"]
                assert attrs["Cave"] == "Water"
                assert attrs["Wall"] == ("Gathering" if folder == "gathering" else "Line " + folder[-1])
                assert type(attrs["Number"]) is int and attrs["Number"] == int(path.stem)
                assert jpeg_info(path.with_suffix(".jpg")) == {"format": "JPEG", "width": 512, "height": 512}
                images.append(path.with_suffix(".jpg").relative_to(ROOT / "dist").as_posix())

    goals = json.loads((ROOT / "dist/goals.json").read_text())
    assert goals == [{"line": n, "goal": (ROOT / f"line-{n}/GOAL.md").read_text().strip()}
                     for n in range(1, 5)]
    gallery = Gallery()
    gallery.feed((ROOT / "dist/index.html").read_text())
    assert gallery.sections == folders and gallery.records == links and gallery.images == images
    assert not gallery.dependencies
    assert (ROOT / "dist/index.html").stat().st_size <= 100_000
    assert not [p for folder in ("gathering", "shared", "dist")
                for p in (ROOT / folder).rglob("*") if p.is_file() and p.stat().st_size > 100_000]
    assert all(r["exitCode"] == 0 for p in (ROOT / "gathering").glob("check-21-*.json")
               for r in json.loads(p.read_text()))
    for entry in json.loads((ROOT / "shared/rpc-batch-review/provenance.json").read_text()):
        source, copy = (ROOT / entry["source"]).read_bytes(), (ROOT / entry["copy"]).read_bytes()
        assert source == copy and hashlib.sha256(copy).hexdigest() == entry["sha256"]
    assert "**none**" in (ROOT / "gathering/COINS.md").read_text()
    assert all((ROOT / name).is_file() for name in ("gathering/REPORT.md", "gathering/COINS.md"))
    review = json.loads((ROOT / "gathering/wall-review-21.json").read_text())
    assert review["wallSha256"] == digest and len(review["unmetVisualRequirements"]) == 2
    assert review["reviewStatus"] == "visually inspected full PNG and decoded JPEG"
    assert wall.read_bytes() == (ROOT / 'artifacts/gathering/wall.png').read_bytes()
    assert review['changedPixels'] == 1153
    assert review['changedPixels'] + review['unchangedPixels'] == 1254*1254
    assert review['allPixelsOutsideAdditionUnchanged'] and review['deepCracksProtected']
    for n in range(1,5):
        manifest = json.loads((ROOT / f'gathering/line-source-hashes-21-{n}.json').read_text())
        baseline = {e['path']: e['sha256'] for e in manifest}
        actual = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (ROOT / f'line-{n}').rglob('*') if p.is_file()}
        assert actual == baseline, f'Line {n} changed'
    for entry in json.loads((ROOT / 'shared/batch-coverage/provenance.json').read_text()):
        raw, copied = (ROOT / entry['source']).read_bytes(), (ROOT / entry['copy']).read_bytes()
        assert raw == copied and hashlib.sha256(raw).hexdigest() == entry['sha256']
    assert all(r['passed'] for r in json.loads((ROOT/'gathering/round-checks-21.json').read_text()))
    assert hashlib.sha256((ROOT/'gathering/live-zto-batch-21.json').read_bytes()).hexdigest() == 'dbeae9bace2b3942e46c8390583466eb7c3d6bd1f3573d97b650eb46f223189b'
    status = subprocess.run(["git", "status", "--short", "--", *folders[:-1]],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    assert not status.stdout, "line folders changed"
    result = {"valid": True, "wall": png_info(wall), "preview": jpeg_info(preview),
              "wallSha256": digest, "paintedRecords": painted_count,
              "placeholderRecords": pending_count, "galleryRecords": len(links),
              "unmetVisualRequirements": review["unmetVisualRequirements"], "lineFoldersUnchanged": True,
              "sharedProvenanceVerified": True}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
