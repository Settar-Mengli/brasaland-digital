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

export async function parseApiError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body !== null && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (Array.isArray(detail)) {
        return formatValidationDetail(detail as ValidationErrorItem[]);
      }
    }
  } catch {
    // Response body was not JSON — fall through to status text.
  }

  if (response.statusText) {
    return response.statusText;
  }

  return `Request failed with status ${response.status}`;
}
