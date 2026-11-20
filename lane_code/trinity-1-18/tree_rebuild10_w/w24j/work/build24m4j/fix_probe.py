from common import *
s=(kit('qd')/'b/rb.py').read_text()
s=s.replace('getattr(loaded, "__file__", None)','loaded.__dict__.get("__file__")').replace('getattr(module, "__file__", None)','module.__dict__.get("__file__")').replace('getattr(module, "__version__", None)','module.__dict__.get("__version__")').replace('getattr(module, "__path__", [])','module.__dict__.get("__path__", [])').replace('getattr(error, "name", None)','(error.name if isinstance(error, ImportError) else None)')
# The native processor chooses its own class from authenticated metadata.
s=s.replace('        probe["status"] = "PASS"','''        if not value.get("probe_only"):
            from student_pilot.carrier_c1_run import processor_for_receipt
            from student_pilot.p3_provenance import load, pinned
            try:
                processor_for_receipt(load(pinned(value["recipe"]["base_model"])), value["config"])
            except ImportError as error:
                raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+(error.name or "transformers")) from error
        probe["status"] = "PASS"''')
for n in NAMES:replace(kit(n)/'b/rb.py',s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
