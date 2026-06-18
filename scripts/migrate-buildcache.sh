#!/usr/bin/env bash
# One-time migration: flatten spack buildcache to one mirror per toolchain.
#
# Before: {toolchain}/slurm/deps/   (blobs + v3 manifests)
# After:  {toolchain}/spack/        (same content, renamed prefix)
#
# Usage:
#   ./scripts/migrate-buildcache.sh [--dry-run]

set -euo pipefail

BUCKET="slurm-factory-spack-buildcache-4b670"
TOOLCHAINS=("resolute" "noble" "jammy" "rockylinux10" "rockylinux9" "rockylinux8")

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN="--dryrun"
    echo "==> DRY RUN (no changes)"
fi

echo "==> Flattening buildcache: {toolchain}/slurm/deps/ → {toolchain}/spack/"
echo "    Bucket: s3://${BUCKET}"
echo

for toolchain in "${TOOLCHAINS[@]}"; do
    SRC="s3://${BUCKET}/${toolchain}/slurm/deps/"
    DST="s3://${BUCKET}/${toolchain}/spack/"

    if ! aws s3 ls "${SRC}" &>/dev/null; then
        echo "--- SKIP ${toolchain}: nothing at ${SRC}"
        continue
    fi

    echo "==> ${toolchain}: syncing slurm/deps/ → spack/"
    aws s3 sync ${DRY_RUN} "${SRC}" "${DST}"
done

echo
echo "==> Sync complete. Rebuilding spack buildcache indexes..."

if [[ -n "${DRY_RUN}" ]]; then
    echo "    (skipped in dry-run mode)"
    exit 0
fi

if ! command -v spack &>/dev/null; then
    echo "WARNING: spack not on PATH — run index rebuild manually:"
    for toolchain in "${TOOLCHAINS[@]}"; do
        echo "  spack mirror add tmp s3://${BUCKET}/${toolchain}/spack && spack buildcache update-index tmp && spack mirror rm tmp"
    done
    exit 0
fi

for toolchain in "${TOOLCHAINS[@]}"; do
    MIRROR_URL="s3://${BUCKET}/${toolchain}/spack"
    MIRROR_NAME="migrate-${toolchain}"

    if ! aws s3 ls "${MIRROR_URL}/v3/" &>/dev/null; then
        echo "--- SKIP ${toolchain}: no v3/ metadata yet"
        continue
    fi

    echo "==> Rebuilding index: ${MIRROR_URL}"
    spack mirror add "${MIRROR_NAME}" "${MIRROR_URL}" 2>/dev/null || true
    spack buildcache update-index "${MIRROR_NAME}"
    spack mirror rm "${MIRROR_NAME}" 2>/dev/null || true
done

echo
echo "==> Done. Old prefixes still exist — delete when verified:"
for toolchain in "${TOOLCHAINS[@]}"; do
    echo "    aws s3 rm --recursive s3://${BUCKET}/${toolchain}/slurm/"
done
