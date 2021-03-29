#!/usr/bin/env python3
from collections import deque
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
import sys
import traceback
from dandi.consts import dandiset_metadata_file
from dandi.metadata import get_default_metadata, nwb2asset
from dandi.models import BareAssetMeta
from dandi.pynwb_utils import validate
from dandi.support.digests import get_digest
from pydantic import ValidationError
import ruamel.yaml

IGNORED_FIELDS = (
    ["dateModified"],
    ["wasGeneratedBy", -1, "identifier"],
    ["wasGeneratedBy", -1, "wasAssociatedWith", 0, "version"],
)


def main():
    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        assert dspath.is_dir()
        outdir = Path(dspath.name)
        pynwb_errs = outdir / "NWB-VALIDATION.errors"
        conversion_errs = outdir / "CONVERSION.errors"
        validation_errs = outdir / "VALIDATION.errors"
        with suppress(FileNotFoundError):
            pynwb_errs.unlink()
        with suppress(FileNotFoundError):
            conversion_errs.unlink()
        with suppress(FileNotFoundError):
            validation_errs.unlink()
        for f in iterfiles(dspath):
            if f == dspath / dandiset_metadata_file:
                continue
            relpath = f.relative_to(dspath)
            print("Processing", f)
            sha256_digest = get_digest(f)
            default_metadata = get_default_metadata(
                f, digest=sha256_digest, digest_type="sha2_256"
            ).json_dict()
            default_metadata["path"] = str(relpath)
            if f.suffix == ".nwb":
                errors = validate(f)
                if errors:
                    print("PYNWB ERRORS:")
                    for e in errors:
                        print(f" - {e}")
                    with pynwb_errs.open("a") as fp:
                        print(relpath, file=fp)
                        for e in errors:
                            print(f" - {e}", file=fp)
                        print(file=fp)
                try:
                    metadata = nwb2asset(
                        f, digest=sha256_digest, digest_type="sha256"
                    ).json_dict()
                except Exception as e:
                    print(f"CONVERSION ERROR: {e}")
                    with conversion_errs.open("a") as fp:
                        print(relpath, file=fp)
                        traceback.print_exc(file=fp)
                        print(file=fp)
                    metadata = default_metadata
                else:
                    metadata["path"] = str(relpath)
                    try:
                        BareAssetMeta(**metadata)
                    except ValidationError as e:
                        print(f"VALIDATION ERROR: {e}")
                        with validation_errs.open("a") as fp:
                            print(relpath, file=fp)
                            traceback.print_exc(file=fp)
                            print(file=fp)
            else:
                metadata = default_metadata
            outfile = (outdir / relpath).with_name(f.name + ".yaml")
            outfile.parent.mkdir(parents=True, exist_ok=True)
            if metadata_differs(yaml, metadata, outfile):
                with outfile.open("w") as fp:
                    yaml.dump(metadata, fp)


def iterfiles(dirpath):
    dirs = deque([dirpath])
    while dirs:
        d = dirs.popleft()
        for p in d.iterdir():
            if p.name.startswith("."):
                continue
            if p.is_dir():
                dirs.append(p)
            else:
                yield p


def metadata_differs(yaml, new_data, filepath):
    try:
        with filepath.open() as fp:
            old_data = yaml.load(fp)
    except FileNotFoundError:
        return True
    new_data = deepcopy(new_data)
    for fieldpath in IGNORED_FIELDS:
        for data in (new_data, old_data):
            for f in fieldpath[:-1]:
                data = data[f]
            data[fieldpath[-1]] = None
    return new_data != old_data


if __name__ == "__main__":
    main()
