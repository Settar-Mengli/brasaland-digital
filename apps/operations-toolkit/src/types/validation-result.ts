/** Validation result type shared across all entity validators. */

/**
 * Result of validating an entity against its business rules.
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}
