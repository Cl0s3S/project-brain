// store.js — État global de l'application (persisté via localStorage)

const Store = (() => {
  const KEY = 'project-brain-v1';

  const defaultState = {
    projects: [],
    farms: [],
    resources: {},
    settings: {
      version: '1.21',
      serverTPS: 20,
      simDistance: 6
    }
  };

  function load() {
    try {
      const saved = localStorage.getItem(KEY);
      return saved ? { ...defaultState, ...JSON.parse(saved) } : { ...defaultState };
    } catch {
      return { ...defaultState };
    }
  }

  function save(state) {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {
      console.warn('Impossible de sauvegarder le store :', e);
    }
  }

  let state = load();

  return {
    get: (key) => key ? state[key] : state,

    set: (key, value) => {
      state[key] = value;
      save(state);
    },

    addProject: (project) => {
      const p = {
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        progress: 0,
        blocks: [],
        ...project
      };
      state.projects.push(p);
      save(state);
      return p;
    },

    getProjects: () => state.projects,

    updateProject: (id, updates) => {
      state.projects = state.projects.map(p =>
        p.id === id ? { ...p, ...updates } : p
      );
      save(state);
    },

    deleteProject: (id) => {
      state.projects = state.projects.filter(p => p.id !== id);
      save(state);
    },

    addFarm: (farm) => {
      const f = {
        id: Date.now().toString(),
        addedAt: new Date().toISOString(),
        ...farm
      };
      state.farms.push(f);
      save(state);
      return f;
    },

    getFarms: () => state.farms,

    updateResource: (itemId, qty) => {
      if (!state.resources) state.resources = {};
      state.resources[itemId] = qty;
      save(state);
    },

    getResources: () => state.resources || {},

    clear: () => {
      state = { ...defaultState };
      localStorage.removeItem(KEY);
    }
  };
})();
