from fractions import Fraction

from .models import Task


class ContradictionGate:
    def check(self, task: Task) -> tuple[bool, str]:
        if task.operation != "solve_system":
            return False, ""

        equations = task.params["eqs"]
        for first in range(len(equations)):
            equation_a = equations[first]
            a1 = Fraction(equation_a["a"])
            d1 = Fraction(equation_a["c"]) - Fraction(equation_a["b"])

            for second in range(first + 1, len(equations)):
                equation_b = equations[second]
                a2 = Fraction(equation_b["a"])
                d2 = Fraction(equation_b["c"]) - Fraction(equation_b["b"])

                if a1 * d2 != a2 * d1:
                    return (
                        True,
                        f"CONTRADICTION: Eq {first} and Eq {second} "
                        "are mutually exclusive.",
                    )

        return False, ""
