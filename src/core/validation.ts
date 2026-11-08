import { Fraction } from './fraction';
import { Task } from './models';

function asFraction(value: any): Fraction {
  if (typeof value === 'boolean') {
    throw new Error('boolean is not a numeric coefficient');
  }
  if (typeof value === 'number' && !Number.isFinite(value)) {
    throw new Error('coefficient must be finite');
  }
  return Fraction.from(value);
}

export class ConstraintValidator {
  validate(task: Task): [boolean, string] {
    if (task.operation !== 'solve_linear' && task.operation !== 'solve_system') {
      return [true, ''];
    }

    if (!task.params || typeof task.params !== 'object' || Array.isArray(task.params)) {
      return [false, 'VALIDATION_ERROR: params must be an object'];
    }

    let equations: any[] = [];
    if (task.operation === 'solve_linear') {
      equations = [task.params];
    } else {
      equations = task.params.eqs;
      if (!Array.isArray(equations) || equations.length === 0) {
        return [false, 'VALIDATION_ERROR: eqs must be a non-empty list'];
      }
    }

    for (let index = 0; index < equations.length; index++) {
      const equation = equations[index];
      const label = task.operation === 'solve_system' ? ` in eq ${index}` : '';

      if (!equation || typeof equation !== 'object' || Array.isArray(equation)) {
        return [false, `VALIDATION_ERROR: equation${label} must be an object`];
      }

      for (const key of ['a', 'b', 'c'] as const) {
        if (!(key in equation)) {
          return [false, `VALIDATION_ERROR: missing coefficient '${key}'${label}`];
        }

        try {
          asFraction(equation[key]);
        } catch {
          return [
            false,
            `VALIDATION_ERROR: coefficient '${key}' must be finite numeric data${label}`,
          ];
        }
      }

      try {
        if (asFraction(equation['a']).isZero()) {
          return [false, `VALIDATION_ERROR: coefficient 'a' cannot be zero${label}`];
        }
      } catch {
        return [
          false,
          `VALIDATION_ERROR: coefficient 'a' must be finite numeric data${label}`,
        ];
      }
    }

    return [true, ''];
  }
}
