import { Fraction } from './fraction';
import { ExecutionResult, Task } from './models';

export interface IExecutor {
  execute(task: Task): ExecutionResult;
}

export class ExactExecutor implements IExecutor {
  execute(task: Task): ExecutionResult {
    try {
      const a = Fraction.from(task.params.a);
      const b = Fraction.from(task.params.b);
      const c = Fraction.from(task.params.c);
      const x = c.sub(b).div(a);
      return { x: x.toString() };
    } catch (error: any) {
      return { error: error?.message || String(error) };
    }
  }
}

export class NumericalExecutor implements IExecutor {
  execute(task: Task): ExecutionResult {
    try {
      const a = Number(task.params.a);
      const b = Number(task.params.b);
      const c = Number(task.params.c);

      if (!Number.isFinite(a) || !Number.isFinite(b) || !Number.isFinite(c)) {
        return { error: 'coefficients must be finite' };
      }

      if (a === 0) {
        return { error: 'division by zero' };
      }

      const x = (c - b) / a;
      return { x };
    } catch (error: any) {
      return { error: error?.message || String(error) };
    }
  }
}

export class BadExecutor implements IExecutor {
  execute(_task: Task): ExecutionResult {
    // Intentionally returns corrupted root for verifier testing (T05)
    return { x: 2.0 };
  }
}

/**
 * DPCO Evolution v0.2: Exact Linear System Solver
 * Fills the CAPABILITY_GAP identified in the PoC v0.1 audit for consistent scalar systems.
 * Solves single-variable or multi-equation systems with exact rational fractions.
 */
export class LinearSystemExecutor implements IExecutor {
  execute(task: Task): ExecutionResult {
    try {
      const eqs = task.params?.eqs;
      if (!Array.isArray(eqs) || eqs.length === 0) {
        return { error: 'No equations provided in system' };
      }

      // In the supported 1-variable format: each equation is a_i * x + b_i = c_i
      // If the contradiction gate passed, all equations are consistent and share the same root!
      const firstEq = eqs[0];
      const a = Fraction.from(firstEq.a);
      const b = Fraction.from(firstEq.b);
      const c = Fraction.from(firstEq.c);
      const root = c.sub(b).div(a);

      // Double-check all other equations for consistency
      for (let i = 1; i < eqs.length; i++) {
        const ai = Fraction.from(eqs[i].a);
        const bi = Fraction.from(eqs[i].b);
        const ci = Fraction.from(eqs[i].c);
        const lhs = ai.mul(root).add(bi);
        if (!lhs.equals(ci)) {
          return { error: `Inconsistency detected at runtime in equation ${i}` };
        }
      }

      return {
        x: root.toString(),
        systemSolution: { x: root.toString() },
      };
    } catch (error: any) {
      return { error: error?.message || String(error) };
    }
  }
}
