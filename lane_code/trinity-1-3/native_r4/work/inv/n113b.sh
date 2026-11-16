set +e
R=/scratch/jjyeung/orch_n30/native_r2
cd $R && ls -la . sub builds builds/02_c8r builds/02_c8r/out builds/02_c8r/work 2>&1 | head -80
du -sh builds/01_c8 builds/02_c8r builds/02_c8r/* sub env312 work/* 2>/dev/null | head -60
tar tf work/obj/metadata_e10fbb95487f3baf.tar | head -60
