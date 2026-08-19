import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'

/* Aturan yang paling berharga di sini adalah `no-undef`: setelah App.jsx dipecah
   menjadi puluhan modul, identifier yang lupa diimpor tidak lagi terlihat saat
   build — ia baru muncul sebagai layar putih di peramban.

   `eslint-plugin-react` sengaja tidak dipakai: versinya belum kompatibel dengan
   ESLint 10 di proyek ini, sementara aturan yang benar-benar dibutuhkan
   (no-undef, no-unused-vars, aturan hook) tidak berasal darinya. */
export default [
  {ignores: ['dist/**', 'node_modules/**']},
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      globals: {...globals.browser, ...globals.es2021},
      parserOptions: {ecmaFeatures: {jsx: true}},
    },
    plugins: {'react-hooks': reactHooks},
    rules: {
      'no-unused-vars': ['error', {argsIgnorePattern: '^_', varsIgnorePattern: '^_'}],
      /* `catch{}` kosong dipakai sengaja di sekitar localStorage: mode privat
         melempar, dan tidak ada yang perlu dilakukan selain melanjutkan. */
      'no-empty': ['error', {allowEmptyCatch: true}],
      'react-hooks/rules-of-hooks': 'error',
      /* Daftar dependensi sengaja hanya peringatan: beberapa efek di halaman ini
         memang dirancang berjalan pada sebagian dependensi saja. */
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
  {
    files: ['**/*.test.{js,jsx}'],
    languageOptions: {globals: {...globals.browser, ...globals.node}},
  },
]
