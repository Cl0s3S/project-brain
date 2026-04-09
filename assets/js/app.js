// app.js — Point d'entrée principal de Project Brain

// ========================
// NAVIGATION
// ========================

function navigateTo(pageId) {
  // Désactiver toutes les pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Activer la page cible
  const page = document.getElementById('page-' + pageId);
  const navItem = document.querySelector('[data-page="' + pageId + '"]');

  if (page) page.classList.add('active');
  if (navItem) navItem.classList.add('active');

  // Mettre à jour le hash
  window.location.hash = pageId;

  // Rafraîchir le contenu
  if (pageId === 'dashboard') renderDashboard();
  if (pageId === 'project') renderProjects();
  if (pageId === 'farms') initFarmPlanner();
  if (pageId === 'resources') initResourceCalculator();
}

// Gestion des liens de navigation
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    navigateTo(item.dataset.page);
  });
});

// Navigation par hash au chargement
function initNavigation() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  navigateTo(hash);
}


// ========================
// DASHBOARD
// ========================

function renderDashboard() {
  const projects = Store.getProjects();
  const farms = Store.getFarms();
  const resources = Store.getResources();

  document.getElementById('stat-projects').textContent = projects.length;
  document.getElementById('stat-farms').textContent = farms.length;
  document.getElementById('stat-resources').textContent = Object.keys(resources).length;

  // Progression globale
  const globalProgress = projects.length > 0
    ? Math.round(projects.reduce((acc, p) => acc + (p.progress || 0), 0) / projects.length)
    : 0;
  document.getElementById('stat-progress').textContent = globalProgress + '%';

  // Projets récents
  const container = document.getElementById('dashboard-projects');
  if (projects.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <span>🗺️</span>
        <p>Aucun projet pour l'instant.</p>
        <button class="btn-primary" onclick="navigateTo('project')">Créer un projet</button>
      </div>`;
    return;
  }

  const recent = [...projects].sort((a, b) =>
    new Date(b.createdAt) - new Date(a.createdAt)
  ).slice(0, 4);

  container.innerHTML = `<div class="projects-grid">${recent.map(projectCard).join('')}</div>`;
}


// ========================
// PROJETS
// ========================

function renderProjects() {
  const projects = Store.getProjects();
  const grid = document.getElementById('projects-grid');

  if (projects.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <span>🗺️</span>
        <p>Aucun projet. Crée-en un !</p>
      </div>`;
    return;
  }

  grid.innerHTML = projects.map(projectCard).join('');
}

function projectCard(p) {
  const badgeClass = 'badge-' + (p.type || 'autre');
  const typeLabel = { build: 'Build', farm: 'Farm', redstone: 'Redstone', autre: 'Autre' }[p.type] || 'Autre';
  return `
    <div class="project-card" onclick="openProject('${p.id}')">
      <span class="badge ${badgeClass}">${typeLabel}</span>
      <h3>${escHtml(p.name)}</h3>
      <p class="proj-desc">${escHtml(p.description || 'Pas de description')}</p>
      <div class="project-progress">
        <div class="progress-bar"><div class="progress-fill" style="width:${p.progress || 0}%"></div></div>
        <span class="progress-label">${p.progress || 0}%</span>
      </div>
    </div>`;
}

// Afficher/masquer le formulaire
document.getElementById('btn-new-project').addEventListener('click', () => {
  document.getElementById('form-new-project').style.display = 'block';
});

function cancelNewProject() {
  document.getElementById('form-new-project').style.display = 'none';
  document.getElementById('proj-name').value = '';
  document.getElementById('proj-desc').value = '';
}

function createProject() {
  const name = document.getElementById('proj-name').value.trim();
  const description = document.getElementById('proj-desc').value.trim();
  const type = document.getElementById('proj-type').value;

  if (!name) {
    alert('Le nom du projet est obligatoire.');
    return;
  }

  Store.addProject({ name, description, type });
  cancelNewProject();
  renderProjects();
}

function openProject(id) {
  const project = Store.getProjects().find(p => p.id === id);
  if (!project) return;
  alert(`Projet : ${project.name}\n\nFonctionnalité complète en cours de développement (v0.1)`);
}


// ========================
// FARM PLANNER
// ========================

let farmsData = [];

async function initFarmPlanner() {
  // Charger les données de farms
  if (farmsData.length === 0) {
    try {
      const res = await fetch('data/farms.json');
      farmsData = await res.json();
    } catch {
      farmsData = [];
    }
  }

  // Peupler le select
  const select = document.getElementById('farm-type');
  select.innerHTML = '<option value="">-- Choisir --</option>' +
    farmsData.map(f => `<option value="${f.id}">${f.name}</option>`).join('');

  // Sliders
  const tpsSlider = document.getElementById('farm-tps');
  const simSlider = document.getElementById('farm-simdist');

  tpsSlider.addEventListener('input', () => {
    document.getElementById('farm-tps-display').textContent = tpsSlider.value + ' TPS';
  });

  simSlider.addEventListener('input', () => {
    document.getElementById('farm-simdist-display').textContent = simSlider.value + ' chunks';
  });
}

function calculateFarm() {
  const farmId = document.getElementById('farm-type').value;
  const tps = parseInt(document.getElementById('farm-tps').value);
  const goal = parseInt(document.getElementById('farm-goal').value) || 0;

  if (!farmId) { alert('Sélectionne un type de farm.'); return; }

  const farm = farmsData.find(f => f.id === farmId);
  if (!farm) return;

  const tpsLoss = (20 - tps) * farm.rates.per_tps_loss;
  const brut = farm.rates.base_per_hour;
  const reel = Math.max(0, brut - tpsLoss);

  document.getElementById('res-brut').textContent = brut.toLocaleString('fr-FR') + ' items/h';
  document.getElementById('res-reel').textContent = reel.toLocaleString('fr-FR') + ' items/h';
  document.getElementById('res-simdist').textContent = farm.rates.min_sim_distance + ' chunks min.';

  if (goal > 0 && reel > 0) {
    const heures = goal / reel;
    document.getElementById('res-temps').textContent = formatDuration(heures);
  } else {
    document.getElementById('res-temps').textContent = '—';
  }
}

function formatDuration(heures) {
  if (heures < 1) return Math.round(heures * 60) + ' min';
  if (heures < 24) return heures.toFixed(1) + ' h';
  const jours = Math.floor(heures / 24);
  const h = Math.round(heures % 24);
  return jours + 'j ' + h + 'h';
}


// ========================
// CALCULATEUR RESSOURCES
// ========================

let blocksData = [];

async function initResourceCalculator() {
  if (blocksData.length === 0) {
    try {
      const res = await fetch('data/blocks.json');
      blocksData = await res.json();
    } catch {
      blocksData = [];
    }
  }

  const select = document.getElementById('goal-item');
  select.innerHTML = '<option value="">-- Choisir un bloc/item --</option>' +
    blocksData.map(b => `<option value="${b.id}">${b.name_fr || b.name}</option>`).join('');
}

function calculateResources() {
  const itemId = document.getElementById('goal-item').value;
  const qty = parseInt(document.getElementById('goal-qty').value) || 0;

  if (!itemId || qty <= 0) { alert('Choisis un item et une quantité.'); return; }

  const plan = resolveRecipe(itemId, qty, blocksData, 0);
  renderResourcePlan(plan);
}

function resolveRecipe(itemId, qty, blocks, depth) {
  const block = blocks.find(b => b.id === itemId);
  const results = [];

  if (!block || block.raw) {
    results.push({
      id: itemId,
      name: block ? (block.name_fr || block.name) : itemId,
      qty: qty,
      step: 'Farmer',
      depth
    });
    return results;
  }

  if (block.craftable && block.recipe) {
    const recipe = block.recipe;
    const batches = Math.ceil(qty / (recipe.output || 1));
    results.push({
      id: itemId,
      name: block.name_fr || block.name,
      qty: qty,
      step: recipe.type === 'furnace' ? 'Fondre' : 'Crafter',
      depth
    });

    if (recipe.ingredients && depth < 5) {
      for (const ing of recipe.ingredients) {
        const subQty = batches * ing.count;
        const sub = resolveRecipe(ing.id, subQty, blocks, depth + 1);
        results.push(...sub);
      }
    }
  }

  return results;
}

function renderResourcePlan(plan) {
  const container = document.getElementById('resources-breakdown');
  const card = document.getElementById('resources-plan');

  if (plan.length === 0) {
    container.innerHTML = '<p style="color:var(--text2)">Aucune donnée disponible.</p>';
    card.style.display = 'block';
    return;
  }

  container.innerHTML = plan.map(item => `
    <div class="resource-item" style="padding-left:${item.depth * 16}px">
      <span class="resource-name">${escHtml(item.name)}</span>
      <span class="resource-qty">${item.qty.toLocaleString('fr-FR')}</span>
      <span class="resource-step">${item.step}</span>
    </div>
  `).join('');

  card.style.display = 'block';
}


// ========================
// UTILS
// ========================

function escHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}


// ========================
// INIT
// ========================

window.addEventListener('DOMContentLoaded', () => {
  initNavigation();
});

window.addEventListener('hashchange', () => {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  navigateTo(hash);
});
