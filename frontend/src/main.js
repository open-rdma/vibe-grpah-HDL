import 'litegraph.js';
import './nodes/rtl-module.js';
import { App } from './app.js';

document.addEventListener('DOMContentLoaded', () => {
  window.__app = new App();
});
