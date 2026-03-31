/**
 * app.js — TaskFlow Frontend JavaScript
 *
 * This file is the "brain" of the frontend. It:
 *  1. Talks to our FastAPI backend via the Fetch API (HTTP requests)
 *  2. Reads data from the API and renders HTML task cards dynamically
 *  3. Handles all user interactions: add, edit, delete, toggle, search, filter
 *
 * How frontend ↔ backend communication works:
 *  - Frontend sends an HTTP request (GET/POST/PUT/DELETE) to the backend URL
 *  - Backend processes it and returns JSON data
 *  - Frontend reads the JSON and updates the UI
 *
 * No page reloads needed! This is the Single-Page App pattern.
 */

'use strict';  // Strict mode: catch common JS mistakes


// ═════════════════════════════════════════════════════════════════════
// CONFIGURATION
//
// API_BASE is empty so all requests use relative URLs (e.g. /tasks).
// This works both locally (served by FastAPI) and on Railway (same origin).
// For local dev with a separate live-server, set: const API_BASE = 'http://localhost:8000';
// ═════════════════════════════════════════════════════════════════════
const API_BASE = '';


// ═════════════════════════════════════════════════════════════════════
// STATE — the app's "memory" at any given moment
// ═════════════════════════════════════════════════════════════════════
let state = {
  tasks: [],             // Array of task objects from the API
  currentFilter: 'all',  // "all" | "completed" | "pending"
  searchQuery: '',       // Current search string
  deleteTargetId: null,  // ID of task pending deletion (for modal)
};


// ═════════════════════════════════════════════════════════════════════
// DOM REFERENCES — grab all the HTML elements we'll need
// (Do once at the top — faster than calling getElementById repeatedly)
// ═════════════════════════════════════════════════════════════════════
const taskForm        = document.getElementById('task-form');
const taskIdInput     = document.getElementById('task-id');
const titleInput      = document.getElementById('task-title');
const descInput       = document.getElementById('task-description');
const prioritySelect  = document.getElementById('task-priority');
const dueDateInput    = document.getElementById('task-due-date');
const submitBtn       = document.getElementById('submit-btn');
const cancelBtn       = document.getElementById('cancel-btn');
const titleError      = document.getElementById('title-error');

const taskList        = document.getElementById('task-list');
const loadingState    = document.getElementById('loading-state');
const emptyState      = document.getElementById('empty-state');
const emptyMessage    = document.getElementById('empty-message');
const headerStats     = document.getElementById('header-stats');
const searchInput     = document.getElementById('search-input');

const filterTabs      = document.querySelectorAll('.filter-tab');
const modalOverlay    = document.getElementById('modal-overlay');
const modalCancelBtn  = document.getElementById('modal-cancel-btn');
const modalConfirmBtn = document.getElementById('modal-confirm-btn');
const toastEl         = document.getElementById('toast');


// ═════════════════════════════════════════════════════════════════════
// API HELPERS
// These functions handle all communication with the backend.
// We use the Fetch API (built into modern browsers).
// ═════════════════════════════════════════════════════════════════════

/**
 * apiRequest — the core fetch wrapper.
 *
 * @param {string} endpoint  - e.g. "/tasks" or "/tasks/5"
 * @param {string} method    - "GET" | "POST" | "PUT" | "DELETE"
 * @param {object} body      - optional request body (for POST/PUT)
 * @returns {Promise<any>}   - parsed JSON response
 *
 * Throws an error if the response status is not 2xx.
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  // Only attach a body for POST and PUT requests
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);

  // If status is not 200-299, read the error and throw it
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // A 204 No Content response has no body — return null
  if (response.status === 204) return null;

  return response.json();
}

// Convenient API method shortcuts
const api = {
  getTasks: (status, search) => {
    const params = new URLSearchParams();
    if (status && status !== 'all') params.append('status', status);
    if (search) params.append('search', search);
    const qs = params.toString() ? `?${params}` : '';
    return apiRequest(`/tasks${qs}`);
  },
  createTask: (data)          => apiRequest('/tasks', 'POST', data),
  updateTask: (id, data)      => apiRequest(`/tasks/${id}`, 'PUT', data),
  deleteTask: (id)            => apiRequest(`/tasks/${id}`, 'DELETE'),
};


// ═════════════════════════════════════════════════════════════════════
// RENDER FUNCTIONS — Build HTML from data and inject into the DOM
// ═════════════════════════════════════════════════════════════════════

/**
 * renderTasks — fetch tasks from API and display them.
 * Called every time state changes (filter, search, add, edit, delete).
 */
async function renderTasks() {
  showLoading(true);
  try {
    const tasks = await api.getTasks(state.currentFilter, state.searchQuery);
    state.tasks = tasks;
    displayTasks(tasks);
    updateHeaderStats();
  } catch (err) {
    showToast('⚠️ Could not load tasks. Is the backend running?', 'error');
    showLoading(false);
  }
}

/**
 * displayTasks — converts task objects to HTML and injects into the DOM.
 * @param {Array} tasks - array of task objects from the API
 */
function displayTasks(tasks) {
  showLoading(false);

  if (tasks.length === 0) {
    taskList.innerHTML = '';
    emptyState.style.display = 'flex';
    // Show different messages depending on context
    emptyMessage.textContent = state.searchQuery
      ? `No tasks match "${state.searchQuery}"`
      : state.currentFilter === 'completed'
      ? 'No completed tasks yet. Keep going!'
      : state.currentFilter === 'pending'
      ? 'No pending tasks. All done! 🎉'
      : 'Add your first task above to get started!';
    return;
  }

  emptyState.style.display = 'none';

  // Build HTML for all tasks and inject at once (efficient DOM update)
  taskList.innerHTML = tasks.map(task => createTaskHTML(task)).join('');

  // Attach event listeners to the newly created elements
  attachTaskListeners();
}

/**
 * createTaskHTML — generates the HTML string for a single task card.
 * @param {object} task - task data from the API
 * @returns {string} HTML string
 */
function createTaskHTML(task) {
  const isCompleted = task.completed;
  const priorityLabel = task.priority || 'medium';

  // Format the due date nicely
  let dueDateHTML = '';
  if (task.due_date) {
    const due = new Date(task.due_date + 'T00:00:00');  // Avoid timezone offset
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const isOverdue = !isCompleted && due < today;
    const formattedDate = due.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
    dueDateHTML = `
      <span class="due-date ${isOverdue ? 'overdue' : ''}">
        ${isOverdue ? '⚠️' : '📅'} ${formattedDate}${isOverdue ? ' (Overdue)' : ''}
      </span>`;
  }

  return `
    <li
      class="task-item priority-${priorityLabel} ${isCompleted ? 'completed' : ''}"
      data-id="${task.id}"
    >
      <!-- Checkbox to toggle completion -->
      <button
        class="task-checkbox ${isCompleted ? 'checked' : ''}"
        data-action="toggle"
        data-id="${task.id}"
        aria-label="${isCompleted ? 'Mark as pending' : 'Mark as completed'}"
        title="${isCompleted ? 'Mark as pending' : 'Mark as completed'}"
      ></button>

      <!-- Task content -->
      <div class="task-body">
        <p class="task-title">${escapeHTML(task.title)}</p>
        ${task.description
          ? `<p class="task-description">${escapeHTML(task.description)}</p>`
          : ''}
        <div class="task-meta">
          <span class="priority-badge ${priorityLabel}">
            ${priorityIcon(priorityLabel)} ${priorityLabel}
          </span>
          ${dueDateHTML}
        </div>
      </div>

      <!-- Edit / Delete buttons -->
      <div class="task-actions">
        <button
          class="action-btn edit-btn"
          data-action="edit"
          data-id="${task.id}"
          aria-label="Edit task"
          title="Edit"
        >✏️</button>
        <button
          class="action-btn delete-btn"
          data-action="delete"
          data-id="${task.id}"
          aria-label="Delete task"
          title="Delete"
        >🗑️</button>
      </div>
    </li>`;
}

/** Returns a small emoji for each priority level */
function priorityIcon(priority) {
  return { low: '🟢', medium: '🟡', high: '🔴' }[priority] || '🟡';
}

/**
 * updateHeaderStats — updates the "X of Y tasks done" counter in the header.
 */
async function updateHeaderStats() {
  // Fetch all tasks (unfiltered) for the totals
  try {
    const all = await api.getTasks();
    const done = all.filter(t => t.completed).length;
    headerStats.textContent = `${done} of ${all.length} tasks done`;
  } catch (_) {
    headerStats.textContent = '';
  }
}


// ═════════════════════════════════════════════════════════════════════
// EVENT HANDLERS
// ═════════════════════════════════════════════════════════════════════

/**
 * attachTaskListeners — delegates click events on task action buttons.
 * Called after tasks are rendered since the buttons are dynamically created.
 */
function attachTaskListeners() {
  taskList.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const action = btn.dataset.action;
      const id = parseInt(btn.dataset.id, 10);

      if (action === 'toggle') await handleToggle(id);
      if (action === 'edit')   handleEdit(id);
      if (action === 'delete') handleDeleteRequest(id);
    });
  });
}

/**
 * handleToggle — flips a task's completed status.
 */
async function handleToggle(id) {
  const task = state.tasks.find(t => t.id === id);
  if (!task) return;

  try {
    await api.updateTask(id, { completed: !task.completed });
    showToast(task.completed ? '↩️ Marked as pending' : '✅ Task completed!', 'success');
    await renderTasks();
  } catch (err) {
    showToast('⚠️ Failed to update task', 'error');
  }
}

/**
 * handleEdit — pre-fills the form with the task's data for editing.
 */
function handleEdit(id) {
  const task = state.tasks.find(t => t.id === id);
  if (!task) return;

  // Populate the form fields
  taskIdInput.value     = task.id;
  titleInput.value      = task.title;
  descInput.value       = task.description || '';
  prioritySelect.value  = task.priority || 'medium';
  dueDateInput.value    = task.due_date || '';

  // Change the button label and show Cancel
  submitBtn.innerHTML = '<span class="btn-icon">💾</span> Save Changes';
  cancelBtn.style.display = 'inline-flex';

  // Scroll to and focus the form
  document.getElementById('add-task-section').scrollIntoView({ behavior: 'smooth' });
  titleInput.focus();
}

/** Resets the form back to "Add Task" mode */
function resetForm() {
  taskForm.reset();
  taskIdInput.value = '';
  titleError.textContent = '';
  submitBtn.innerHTML = '<span class="btn-icon">＋</span> Add Task';
  cancelBtn.style.display = 'none';
}

/**
 * handleDeleteRequest — shows the confirmation modal before deleting.
 */
function handleDeleteRequest(id) {
  state.deleteTargetId = id;
  modalOverlay.style.display = 'flex';
}

// ─── FORM SUBMIT ────────────────────────────────────
taskForm.addEventListener('submit', async (e) => {
  e.preventDefault();  // Prevent the default browser form submission

  // Client-side validation
  const title = titleInput.value.trim();
  if (!title) {
    titleError.textContent = 'Task title is required.';
    titleInput.focus();
    return;
  }
  titleError.textContent = '';

  // Build the request payload
  const payload = {
    title,
    description:  descInput.value.trim() || null,
    priority:     prioritySelect.value,
    due_date:     dueDateInput.value || null,
  };

  const editingId = taskIdInput.value;

  try {
    if (editingId) {
      // ── UPDATE existing task ──
      await api.updateTask(parseInt(editingId, 10), payload);
      showToast('✏️ Task updated!', 'success');
    } else {
      // ── CREATE new task ──
      await api.createTask(payload);
      showToast('✅ Task added!', 'success');
    }

    resetForm();
    await renderTasks();
  } catch (err) {
    showToast(`⚠️ ${err.message}`, 'error');
  }
});

// ─── CANCEL EDIT ──────────────────────────────────
cancelBtn.addEventListener('click', resetForm);

// ─── SEARCH (with debounce — waits 350ms after typing stops) ──────────────
let searchTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.searchQuery = searchInput.value.trim();
    renderTasks();
  }, 350);
});

// ─── FILTER TABS ──────────────────────────────────
filterTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove active from all, add to clicked
    filterTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    state.currentFilter = tab.dataset.filter;
    renderTasks();
  });
});

// ─── DELETE MODAL ─────────────────────────────────
modalCancelBtn.addEventListener('click', () => {
  state.deleteTargetId = null;
  modalOverlay.style.display = 'none';
});

modalConfirmBtn.addEventListener('click', async () => {
  const id = state.deleteTargetId;
  modalOverlay.style.display = 'none';
  state.deleteTargetId = null;

  if (!id) return;

  try {
    await api.deleteTask(id);
    showToast('🗑️ Task deleted', 'success');
    await renderTasks();
  } catch (err) {
    showToast('⚠️ Failed to delete task', 'error');
  }
});

// Close modal by clicking the backdrop
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) {
    state.deleteTargetId = null;
    modalOverlay.style.display = 'none';
  }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modalOverlay.style.display !== 'none') {
    state.deleteTargetId = null;
    modalOverlay.style.display = 'none';
  }
});


// ═════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═════════════════════════════════════════════════════════════════════

/** Show or hide the loading spinner */
function showLoading(visible) {
  loadingState.style.display = visible ? 'flex' : 'none';
  if (visible) {
    taskList.innerHTML = '';
    emptyState.style.display = 'none';
  }
}

/**
 * showToast — displays a brief notification at the bottom of the screen.
 * @param {string} message - text to display
 * @param {string} type    - "success" | "error"
 */
let toastTimer;
function showToast(message, type = 'success') {
  toastEl.textContent = message;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.className = 'toast';  // Hide by removing 'show'
  }, 3000);
}

/**
 * escapeHTML — prevents XSS attacks by converting dangerous characters.
 * Always escape user-provided text before inserting into innerHTML!
 * @param {string} str - raw user input
 * @returns {string} safe HTML string
 */
function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}


// ═════════════════════════════════════════════════════════════════════
// INIT — Run when the page loads
// ═════════════════════════════════════════════════════════════════════
renderTasks();
