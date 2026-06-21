import type { AppSettings } from '../api/types';

export type UiPreferences = AppSettings['ui'];

export function resolveTheme(theme: string | undefined): 'dark' | 'light' {
  if (theme === 'light') return 'light';
  if (theme === 'system') {
    return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  return 'dark';
}

export function applyUiPreferences(ui: Partial<UiPreferences> | undefined): void {
  const theme = resolveTheme(ui?.theme);
  const density = ui?.density === 'compact' ? 'compact' : 'comfortable';
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.density = density;
}
