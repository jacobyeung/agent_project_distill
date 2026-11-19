"""Stable refusal codes for model/program and perception mismatches."""
class ProgramRefusal(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)
