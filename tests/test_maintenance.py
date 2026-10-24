from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def workspace(tmp_path):
    store = ResearchStore(tmp_path / "workspace")
    item = store.import_bytes("finding.txt", b"Finding: 12 units.", "upload:finding.txt")
    service = ResearchService(store)
    claim = service.create_claim("There are 12 units.", store.list_passages(item["source_id"])[0]["id"])
    service.review_claim(claim["id"], "approved", "Reviewed.")
    return store, item


def test_backup_restore_preserves_claims_originals_and_ids(tmp_path):
    from sourcepilot.maintenance import backup_workspace, diagnose, restore_workspace

    store, item = workspace(tmp_path)
    archive = tmp_path / "backup.zip"
    backup_workspace(store, archive)
    restored = restore_workspace(archive, tmp_path / "restored")
    assert diagnose(restored)["healthy"] is True
    assert ResearchService(restored).get_claim(1)["status"] == "approved"
    assert restored.original_path(item["sha256"]).read_bytes() == b"Finding: 12 units."
    assert restored.list_passages(item["source_id"])[0]["id"] == 1
    with pytest.raises(FileExistsError):
        backup_workspace(store, archive)
    with pytest.raises(FileExistsError):
        restore_workspace(archive, restored.workspace)


def test_doctor_identifies_corrupt_objects_and_backup_refuses_them(tmp_path):
    from sourcepilot.maintenance import backup_workspace, diagnose

    store, item = workspace(tmp_path)
    Path(item["object_path"]).write_bytes(b"altered")
    result = diagnose(store)
    assert result["healthy"] is False
    assert result["issues"][0]["version_id"] == item["version_id"]
    output = tmp_path / "bad.zip"
    with pytest.raises(ValueError, match="integrity"):
        backup_workspace(store, output)
    assert not output.exists()


@pytest.mark.parametrize("member", ["../escape", "/absolute", "C:/outside", "objects\\escape", "unexpected.txt"])
def test_restore_rejects_unexpected_archive_members(tmp_path, member):
    from sourcepilot.maintenance import restore_workspace

    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("manifest.json", json.dumps({"format": 1, "files": {}}))
        output.writestr(member, b"unsafe")
    destination = tmp_path / "restored"
    with pytest.raises(ValueError):
        restore_workspace(archive, destination)
    assert not destination.exists()


def test_restore_rejects_corrupt_member_without_partial_destination(tmp_path):
    from sourcepilot.maintenance import backup_workspace, restore_workspace

    store, _ = workspace(tmp_path)
    good = tmp_path / "good.zip"
    backup_workspace(store, good)
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(good) as source, zipfile.ZipFile(bad, "w") as target:
        for name in source.namelist():
            target.writestr(name, source.read(name) if name == "manifest.json" else b"corrupted")
    with pytest.raises(ValueError, match="checksum|size"):
        restore_workspace(bad, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
