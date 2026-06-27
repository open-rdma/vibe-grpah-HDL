export interface KnowledgeContext {
  entity: Record<string, any>;
}

export class KnowledgeMerger {
  /**
   * Merge knowledge levels from outer to inner.
   * `levels` is ordered outermost-first (system, project, graph, node, port).
   * Empty/undefined levels are skipped.
   * `context.entity` provides data for {{variable}} interpolation on the
   * innermost level (typically the port or node being rendered).
   */
  merge(levels: (string | undefined)[], context: KnowledgeContext, template?: string): string {
    const parts: string[] = [];
    for (let i = 0; i < levels.length; i++) {
      const raw = levels[i];
      if (!raw || raw.trim() === '') continue;
      parts.push(this._interpolate(raw, context.entity));
    }
    const body = parts.join('\n\n---\n\n');
    if (template && body) {
      return template.replace(/\{\{children\}\}/g, body);
    }
    return body;
  }

  /**
   * Render a template string with {{variable}} interpolation.
   * Unresolved variables are left as-is.
   */
  _interpolate(template: string, entity: Record<string, any>): string {
    return template.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (_match, path: string) => {
      return this._resolve(entity, path);
    });
  }

  /**
   * Resolve a dotted path like "properties.clock_freq_mhz" from the entity.
   * Returns the string value, or the original {{pattern}} if unresolvable.
   */
  _resolve(entity: Record<string, any>, path: string): string {
    const parts = path.split('.');
    let current: any = entity;
    for (const part of parts) {
      if (current == null || typeof current !== 'object') {
        return `{{${path}}}`;
      }
      if (part in current) {
        current = current[part];
      } else {
        return `{{${path}}}`;
      }
    }
    if (current == null) return `{{${path}}}`;
    return String(current);
  }
}
