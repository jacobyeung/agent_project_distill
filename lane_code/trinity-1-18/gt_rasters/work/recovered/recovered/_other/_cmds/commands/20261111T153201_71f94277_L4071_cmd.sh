<!-- recovered by seal_plan: transcript=71f94277 line=4071 utc=2026-11-11T15:32:01.985Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > vla_libero/inbox/${T}_ORCH_two_cache_bugs.md <<'EOF'
# ORCH: two more breaks from the integration test, both in vl_data_patch.py (where-cache reader)
/scratch/jjyeung/orch_cd/vla_integ/out/BREAKS.md (rewritten against your current files) and patches out/00_cache_schema.patch, then out/10_cache_root.patch:
1. vl_data_patch.py:44 memoizes by episode id only, while the provider's cache pins each root to one provider (vla_where/cache.py:100, schema 9): changing roots in one process returns stale geometry, so a whole U1 or ablation run could read the wrong provider. Patch 10 keys by resolved root and episode.
2. vl_data_patch.py:42 checks record hashes but ignores MANIFEST.json: a cache written under another schema version is accepted. Patch 00 refuses a wrong `vla_schema_v2/where_cache_key` before lookup.
Apply both (Trinity and Orchard copies), rerun your tests and /scratch/jjyeung/orch_cd/vla_integ/work/run_integ.sh, and include them in the RESULT for my earlier note. CPU only.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) vla_integ rerun 1531Z: the five earlier contract regressions pass against vla_libero's current files; two new breaks in vla_libero's where-cache reader (memoization by episode id only crosses provider roots; MANIFEST schema version unchecked), patches 00 and 10 handed to vla_libero." >> ORCH_HANDOFF.md