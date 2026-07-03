import type { ReactNode } from 'react';

type FormFieldProps = {
  id: string;
  label: string;
  error?: string | undefined;
  highlighted?: boolean;
  helperText?: string | undefined;
  children: ReactNode;
};

export default function FormField({
  id,
  label,
  error,
  highlighted = false,
  helperText,
  children,
}: FormFieldProps) {
  return (
    <div
      className={
        highlighted
          ? 'rounded-md border border-brasaland-ember ring-2 ring-brasaland-ember/20 bg-brasaland-ember/5 p-3'
          : undefined
      }
    >
      <label htmlFor={id} className="block text-sm font-medium mb-1">
        {label}
      </label>
      {children}
      {helperText ? <p className="text-sm text-brasaland-ember mt-1">{helperText}</p> : null}
      {error ? (
        <p role="alert" className="text-sm text-brasaland-error mt-1">
          {error}
        </p>
      ) : null}
    </div>
  );
}

const inputClassName =
  'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';

export function formInputClassName(): string {
  return inputClassName;
}
