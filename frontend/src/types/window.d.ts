// Global window augmentation — exposes app singletons to litegraph.js callbacks.
//
// Using `any` for the app singletons is deliberate: a structural type would
// have to mirror App exactly, and importing App creates a type-only cycle
// (window.d.ts → app.ts → boundary-nodes.ts → window.__app).  The cast here
// is a single global registration point; every consumer gets typed access.
//
// IMPORTANT: these are intentionally loose — the alternative was `(window as
// any).__app` scattered across 5+ files.  One global `any` is better than
// per-file type erasure.

declare global {
  interface Window {
    __app?: Record<string, any>;
    __connectionValidator?: Record<string, any>;
  }
}

export {};
