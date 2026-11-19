from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'out/kit_timing/write_plan.py';s=p.read_text()
s=s.replace("    with Path(args.out).open('x') as output:\n        output.write(json.dumps(result,indent=2)+'\\n')", "    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))\n    from privacy import scrub\n    with Path(args.out).open('x') as output:\n        output.write(json.dumps(scrub(result),indent=2)+'\\n')")
s=s.replace("if __name__ == '__main__':\n    main()", "if __name__ == '__main__':\n    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))\n    from privacy import filter_streams\n    filter_streams()\n    main()")
p.write_text(s)
p=ROOT/'out/kit_timing/replay_compare.py';s=p.read_text()
s=s.replace("if __name__ == '__main__':\n    main()", "if __name__ == '__main__':\n    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))\n    from privacy import filter_streams\n    filter_streams()\n    main()")
p.write_text(s)
