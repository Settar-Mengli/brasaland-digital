export type FieldError = {
  field: string;
  message: string;
};

type ValidationErrorItem = {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
};

function formatValidationDetail(detail: ValidationErrorItem[]): string {
  return detail
    .map((item) => {
      if (typeof item.msg === 'string') {
        const field = item.loc?.at(-1);
        return field !== undefined ? `${String(field)}: ${item.msg}` : item.msg;
      }
      return String(item);
    })
    .join('; ');
}

function isFieldError(value: unknown): value is FieldError {
  return (
    value !== null &&
    typeof value === 'object' &&
    'field' in value &&
    'message' in value &&
    typeof (value as FieldError).field === 'string' &&
    typeof (value as FieldError).message === 'string'
  );
}

export function extractFieldErrors(detail: unknown): FieldError[] {
  if (detail === null || typeof detail !== 'object' || !('errors' in detail)) {
    return [];
  }

  const errors = (detail as { errors: unknown }).errors;
  if (!Array.isArray(errors)) {
    return [];
  }

  return errors.filter(isFieldError);
}

export async function parseApiError(response: Response): Promise<string> {
  const parsed = await parseApiErrorResponse(response);
  return parsed.message;
}

export async function parseApiErrorResponse(
  response: Response,
): Promise<{ message: string; fieldErrors: FieldError[] }> {
  try {
    const body: unknown = await response.json();
    if (body !== null && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail;

      const fieldErrors = extractFieldErrors(detail);
      if (fieldErrors.length > 0) {
        return {
          message: 'Please check the form and try again.',
          fieldErrors,
        };
      }

      if (typeof detail === 'string') {
        return { message: detail, fieldErrors: [] };
      }

      if (Array.isArray(detail)) {
        return {
          message: formatValidationDetail(detail as ValidationErrorItem[]),
          fieldErrors: [],
        };
      }
    }
  } catch {
    // Response body was not JSON — fall through to status text.
  }

  if (response.statusText) {
    return { message: response.statusText, fieldErrors: [] };
  }

  return { message: `Request failed with status ${response.status}`, fieldErrors: [] };
}
