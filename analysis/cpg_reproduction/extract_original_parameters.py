"""Read one original HDF5 replicate inside a stored ZIP member via bounded HTTP ranges.

Neither the entire HDF5 CRC nor the complete ZIP MD5 can be verified for a slice.
Keeps the downloaded original YAML records, adding derived arrays and explicit provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import zipfile
from datetime import datetime, timezone

import h5py
import numpy as np
import download_archive_config as dl

MEMBER = dl.PREFIX + "ckpt/neuron_params.h5"


class BoundedMember(io.RawIOBase):
    def __init__(self, remote, offset, size, budget):
        self.remote = remote
        self.offset = offset
        self.size = size
        self.position = 0
        self.cache = {}
        self.page_size = 64 * 1024
        self.budget = budget
        self.bytes_fetched = 0
        self.ranges = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def writable(self):
        return False

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if self.position < 0:
            raise ValueError("Negative member offset")
        return self.position

    def read(self, size=-1):
        size = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if size <= 0:
            return b""
        output = bytearray()
        stop = self.position + size
        while self.position < stop:
            page = self.position // self.page_size
            if page not in self.cache:
                start = page * self.page_size
                count = min(self.page_size, self.size - start)
                if self.bytes_fetched + count > self.budget:
                    raise RuntimeError(f"HDF5 range budget exhausted at {self.bytes_fetched} bytes; no automatic full-file download")
                self.remote.seek(self.offset + start)
                data = self.remote.read(count)
                self.cache[page] = data
                self.bytes_fetched += len(data)
                self.ranges.append({"memberOffset": start, "archiveOffset": self.offset + start,
                                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            data = self.cache[page]
            inside = self.position - page * self.page_size
            length = min(stop - self.position, len(data) - inside)
            output.extend(data[inside:inside + length])
            self.position += length
        return bytes(output)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def stored_member(remote):
    with zipfile.ZipFile(remote) as archive:
        info = archive.getinfo(MEMBER)
    if info.compress_type != zipfile.ZIP_STORED or info.compress_size != info.file_size:
        raise RuntimeError("Random access requires an uncompressed ZIP_STORED member")
    if info.flag_bits & 1:
        raise RuntimeError("Encrypted ZIP member is unsupported")
    remote.seek(info.header_offset)
    header = remote.read(30)
    signature, version, flags, method, mtime, mdate, crc, csize, usize, nlen, elen = struct.unpack("<4s5H3I2H", header)
    if signature != b"PK\x03\x04" or method != zipfile.ZIP_STORED:
        raise RuntimeError("ZIP local header disagrees with central-directory storage mode")
    name = remote.read(nlen)
    if name.decode("utf-8" if flags & 0x800 else "cp437") != MEMBER:
        raise RuntimeError("ZIP local member name disagrees with directory")
    return info, info.header_offset + 30 + nlen + elen


def metadata(item):
    return {"shape": list(item.shape), "dtype": str(item.dtype), "chunks": list(item.chunks) if item.chunks else None,
            "compression": item.compression, "compressionOptions": item.compression_opts,
            "logicalBytes": item.size * item.dtype.itemsize,
            "storedBytes": None, "storageSizeOmittedReason": "Avoid enumerating every compressed chunk for a metadata-only range inspection."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--budget-mb", type=float, default=8)
    args = parser.parse_args()
    if not 0 < args.budget_mb <= 16:
        raise ValueError("Explicit bounded range budget must be within 0–16 MiB")
    if dl.STATUS.exists():
        dl.STATE.update(json.loads(dl.STATUS.read_text(encoding="utf-8")))
    before = dl.STATE["bytesDownloaded"]
    dl.report(phase="preparing_hdf5", status="running", totalBytes=None, error=None, mode="http_range_hdf5",
              progressPrefix="Originale HDF5-Parameter per Range", parameterTransferBudgetBytes=int(args.budget_mb * 1024 ** 2),
              detail="Lese Original-HDF5-Verzeichnis und höchstens die erste Parameterziehung; keine neue Zufallsziehung.")
    try:
        remote = dl.RemoteZip()
        info, offset = stored_member(remote)
        member = BoundedMember(remote, offset, info.file_size, int(args.budget_mb * 1024 ** 2))
        inventory = {}
        arrays = {}
        selections = {}
        dl.report(phase="inspecting_hdf5", detail="HDF5-Datensatznamen, Formen und Chunkgrößen werden per Range geprüft.")
        with h5py.File(member, "r") as h5:
            root_keys = list(h5.keys())
            print(json.dumps({"rootKeys": root_keys[:100], "rootKeyCount": len(root_keys), "hdf5BytesFetched": member.bytes_fetched}), flush=True)
            dl.atomic_json(dl.TARGET / "original_hdf5_root_keys.json", {"rootKeys": root_keys, "hdf5BytesFetched": member.bytes_fetched})
            # Do not recursively enumerate replicated groups or W-mask chunk trees.
            for name in root_keys:
                if name in ["W", "W_mask"]:
                    inventory[name] = {"metadataSkipped": True, "reason": "Large matrix/mask dataset is not required for first-replicate parameter extraction."}
                    continue
                obj = h5[name]
                if isinstance(obj, h5py.Dataset):
                    inventory[name] = metadata(obj)
                    print(json.dumps({"dataset": name, **inventory[name], "hdf5BytesFetched": member.bytes_fetched}), flush=True)
                else:
                    child_keys = list(obj.keys())
                    print(json.dumps({"group": name, "childKeys": child_keys[:20], "childKeyCount": len(child_keys)}), flush=True)
                    for child in child_keys:
                        if child.rsplit("/", 1)[-1] in ["tau", "a", "threshold", "fr_cap", "input_currents", "seeds"]:
                            item = obj[child]
                            if isinstance(item, h5py.Dataset):
                                inventory[f"{name}/{child}"] = metadata(item)
            inventory_record = {"schema": "fly.cpg-original-hdf5-inventory.v1", "sourceURL": dl.SOURCE,
                                "zipMember": MEMBER, "memberArchiveOffset": offset, "memberBytes": info.file_size,
                                "zipCompressionMethod": info.compress_type, "memberCrc32Expected": f"{info.CRC:08x}",
                                "memberCrc32Verified": False, "datasets": inventory,
                                "metadataRangeBytes": member.bytes_fetched}
            dl.atomic_json(dl.TARGET / "original_hdf5_inventory.json", inventory_record)
            print(json.dumps(inventory_record, ensure_ascii=False, indent=2), flush=True)
            if not args.inspect_only:
                by_basename = {}
                for name in inventory:
                    base = name.rsplit("/", 1)[-1]
                    if base in by_basename:
                        raise ValueError(f"Ambiguous dataset basename: {base}")
                    by_basename[base] = name
                for key in ["tau", "a", "threshold", "fr_cap"]:
                    path = by_basename.get(key)
                    if path is None:
                        raise KeyError(f"Required original dataset is absent: {key}")
                    dataset = h5[path]
                    if dataset.shape != (1024, 4963):
                        raise ValueError(f"Unexpected original replicate shape {path}: {dataset.shape}")
                    dl.report(phase="extracting_original_parameters", detail=f"Originalreplikat 0: {key}, 4.963 unveränderte Zellwerte.")
                    arrays[key] = np.asarray(dataset[0:1, :])
                    selections[key] = {"dataset": path, "selection": "[0:1, :]", "sourceShape": list(dataset.shape),
                                       "derivedShape": list(arrays[key].shape), "dtype": str(arrays[key].dtype),
                                       "arrayBytesSha256": hashlib.sha256(arrays[key].tobytes(order="C")).hexdigest()}
                for key in ["input_currents", "seeds"]:
                    path = by_basename.get(key)
                    if path is None:
                        continue
                    dataset = h5[path]
                    if key == "input_currents" and dataset.shape == (1, 1024, 4963):
                        selection = "[0:1, 0:1, :]"
                        arrays[key] = np.asarray(dataset[0:1, 0:1, :])
                    elif key == "seeds" and dataset.shape[0] == 1024:
                        selection = "[0:1, ...]"
                        arrays[key] = np.asarray(dataset[0:1, ...])
                    else:
                        raise ValueError(f"Unexpected optional original shape {path}: {dataset.shape}")
                    selections[key] = {"dataset": path, "selection": selection, "sourceShape": list(dataset.shape),
                                       "derivedShape": list(arrays[key].shape), "dtype": str(arrays[key].dtype),
                                       "arrayBytesSha256": hashlib.sha256(arrays[key].tobytes(order="C")).hexdigest()}
        # HDF5 has closed before the backing Python file-like object is closed.
        if arrays:
            output = dl.TARGET / "original_parameters_replicate0.npz"
            np.savez_compressed(output, **arrays)
            file_record = {"path": str(output.relative_to(dl.ROOT)).replace("\\", "/"),
                           "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                           "derivedArtifact": True, "crc32Verified": False}
            dl.STATE["files"] = [f for f in dl.STATE["files"] if f.get("path") != file_record["path"]] + [file_record]
        provenance = {"schema": "fly.cpg-original-parameter-extract.v1", "sourceURL": dl.SOURCE,
                      "runId": "33241778", "replicateIndex": 0, "zipMember": MEMBER,
                      "memberArchiveOffset": offset, "memberBytes": info.file_size,
                      "memberCrc32Expected": f"{info.CRC:08x}", "memberCrc32Verified": False,
                      "fullArchiveMd5Verified": False, "httpRangeBytesThisOperation": dl.STATE["bytesDownloaded"] - before,
                      "hdf5BytesFetched": member.bytes_fetched, "rangeBudgetBytes": member.budget,
                      "rangeManifest": member.ranges, "datasetSelections": selections,
                      "output": file_record if arrays else None,
                      "parametersResampled": False, "valuesTransformed": False,
                      "sourceCodeExpectedState": "Original prepare_neuron_params applies surface-size scaling before HDF5 storage; do not reapply it.",
                      "verifiedExtent": "HTTPS Content-Range boundaries checked; hashes describe retrieved ranges and derived arrays. Whole-member CRC32 and whole-archive MD5 were not verifiable from this partial retrieval.",
                      "retrievedAt": datetime.now(timezone.utc).isoformat()}
        name = "original_parameter_extract_provenance.json" if arrays else "original_hdf5_inspection_provenance.json"
        dl.atomic_json(dl.TARGET / name, provenance)
        text = f"Fertig: {'erste originale Parameterziehung' if arrays else 'Original-HDF5-Verzeichnis'} per Range gelesen; {member.bytes_fetched:,} HDF5-Bytes statt104 MB. Voll-HDF5-CRC nicht geprüft."
        dl.report(phase="complete", status="complete", totalBytes=dl.STATE["bytesDownloaded"], detail=text, error=None)
        print(json.dumps({"datasets": inventory, "selections": selections, "bytesThisOperation": provenance["httpRangeBytesThisOperation"],
                          "output": provenance["output"]}, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        dl.report(phase="failed", status="failed", error=f"{type(exc).__name__}: {exc}",
                  detail="Begrenzter HDF5-Zugriff abgebrochen; vorhandene YAML-Dateien bleiben verfügbar. Kein vollständiger HDF5-Download gestartet.")
        raise


if __name__ == "__main__":
    main()
