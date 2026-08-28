import { defineConfig, globalIgnores } from 'eslint/config';
import tseslint from 'typescript-eslint';

const eslintConfig = defineConfig([
  ...tseslint.configs.recommended,
  globalIgnores([
    '**/.next/**',
    '**/out/**',
    '**/node_modules/**',
    '**/dist/**',
    '**/build/**',
    'next-env.d.ts',
  ]),
]);

export default eslintConfig;
