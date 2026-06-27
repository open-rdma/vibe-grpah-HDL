const STORAGE_KEY = 'recent-projects';
const MAX_ENTRIES = 10;

const RecentProjects = {
  getRecentProjects(): string[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.filter((p: unknown) => typeof p === 'string' && p.length > 0);
    } catch {
      return [];
    }
  },

  addRecentProject(path: string): void {
    if (!path) return;
    const list = this.getRecentProjects().filter((p) => p !== path);
    list.unshift(path);
    if (list.length > MAX_ENTRIES) list.length = MAX_ENTRIES;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    } catch {
      // localStorage full or unavailable — silently ignore
    }
  }
};

export { RecentProjects };
