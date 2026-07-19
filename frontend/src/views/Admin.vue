<script setup>
import { ref, onMounted } from 'vue'

import { api } from '../api.js'
import { toast } from '../toast.js'

const items = ref([])
const users = ref([])

const newItem = ref({ name: '', brand: '', purchase_date: '', status: 'Available', notes: '' })
const newUser = ref({ email: '', password: '', is_admin: false })

async function load() {
  try {
    items.value = await api.listHardware({ sort_by: 'id' })
    users.value = await api.listUsers()
  } catch (e) {
    toast.error(e)
  }
}

async function addItem() {
  if (!newItem.value.name.trim()) return toast.error(new Error('Name is required'))
  try {
    const payload = { ...newItem.value }
    if (!payload.purchase_date) payload.purchase_date = null
    await api.createHardware(payload)
    toast.show('Item added')
    newItem.value = { name: '', brand: '', purchase_date: '', status: 'Available', notes: '' }
    load()
  } catch (e) {
    toast.error(e)
  }
}

async function toggleRepair(item) {
  try {
    await api.toggleRepair(item.id)
    load()
  } catch (e) {
    toast.error(e)
  }
}

async function remove(item) {
  if (!confirm(`Delete “${item.name}”?`)) return
  try {
    await api.deleteHardware(item.id)
    toast.show('Item deleted')
    load()
  } catch (e) {
    toast.error(e)
  }
}

async function addUser() {
  try {
    await api.createUser(newUser.value)
    toast.show(`Account created for ${newUser.value.email}`)
    newUser.value = { email: '', password: '', is_admin: false }
    load()
  } catch (e) {
    toast.error(e)
  }
}

onMounted(load)
</script>

<template>
  <div class="container">
    <h1 style="margin-bottom: 18px">Admin Command Center</h1>

    <div class="grid">
      <!-- Add hardware -->
      <div class="card">
        <h2>Add hardware</h2>
        <div class="form">
          <input v-model="newItem.name" placeholder="Name *" />
          <input v-model="newItem.brand" placeholder="Brand" />
          <input v-model="newItem.purchase_date" type="date" />
          <select v-model="newItem.status">
            <option>Available</option>
            <option>In Use</option>
            <option>Repair</option>
          </select>
          <input v-model="newItem.notes" placeholder="Notes (optional)" />
          <button class="primary" @click="addItem">Add item</button>
        </div>
      </div>

      <!-- Create account -->
      <div class="card">
        <h2>Create account</h2>
        <div class="form">
          <input v-model="newUser.email" type="email" placeholder="email@booksy.com" />
          <input v-model="newUser.password" type="password" placeholder="Password" />
          <label class="check">
            <input v-model="newUser.is_admin" type="checkbox" /> Admin privileges
          </label>
          <button class="primary" @click="addUser">Create account</button>
        </div>

        <h2 style="margin-top: 20px">Users ({{ users.length }})</h2>
        <ul class="users">
          <li v-for="u in users" :key="u.id">
            {{ u.email }}
            <span v-if="u.is_admin" class="badge inuse">admin</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Manage hardware -->
    <div class="card" style="margin-top: 16px">
      <h2>Manage hardware ({{ items.length }})</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Status</th>
            <th>Flags</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="muted">{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td><span class="badge" :class="item.status.replace(' ', '').toLowerCase()">{{ item.status }}</span></td>
            <td class="flag">{{ item.data_flag || '—' }}</td>
            <td class="actions">
              <button
                class="ghost"
                :disabled="item.status === 'In Use'"
                :title="item.status === 'In Use' ? 'Return it first' : ''"
                @click="toggleRepair(item)"
              >
                {{ item.status === 'Repair' ? 'Clear repair' : 'Mark repair' }}
              </button>
              <button class="danger" @click="remove(item)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 780px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
.form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
}
.check input {
  width: auto;
}
.users {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.users li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.actions {
  text-align: right;
  white-space: nowrap;
}
.actions button {
  margin-left: 6px;
}
</style>
