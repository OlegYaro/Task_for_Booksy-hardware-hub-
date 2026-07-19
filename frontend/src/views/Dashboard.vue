<script setup>
import { ref, computed, onMounted } from 'vue'

import { api } from '../api.js'
import { store } from '../store.js'
import { toast } from '../toast.js'

const items = ref([])
const loading = ref(false)

// Filters / sorting
const statusFilter = ref('')
const brandFilter = ref('')
const search = ref('')
const sortBy = ref('id')
const order = ref('asc')

// AI search
const aiQuery = ref('')
const aiResult = ref(null)
const aiSearching = ref(false)

// Auditor
const audit = ref(null)
const auditing = ref(false)

const brands = computed(() =>
  [...new Set(items.value.map((i) => i.brand).filter(Boolean))].sort()
)

async function load() {
  loading.value = true
  try {
    items.value = await api.listHardware({
      status: statusFilter.value,
      brand: brandFilter.value,
      search: search.value,
      sort_by: sortBy.value,
      order: order.value,
    })
  } catch (e) {
    toast.error(e)
  } finally {
    loading.value = false
  }
}

function setSort(col) {
  if (sortBy.value === col) {
    order.value = order.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = col
    order.value = 'asc'
  }
  load()
}

async function rent(item) {
  try {
    await api.rent(item.id)
    toast.show(`Rented “${item.name}”`)
    load()
  } catch (e) {
    toast.error(e)
  }
}

async function returnItem(item) {
  try {
    await api.returnItem(item.id)
    toast.show(`Returned “${item.name}”`)
    load()
  } catch (e) {
    toast.error(e)
  }
}

async function runSearch() {
  if (!aiQuery.value.trim()) return
  aiSearching.value = true
  aiResult.value = null
  try {
    aiResult.value = await api.search(aiQuery.value)
  } catch (e) {
    toast.error(e)
  } finally {
    aiSearching.value = false
  }
}

function clearSearch() {
  aiQuery.value = ''
  aiResult.value = null
}

async function runAudit() {
  auditing.value = true
  try {
    audit.value = await api.audit()
  } catch (e) {
    toast.error(e)
  } finally {
    auditing.value = false
  }
}

const displayed = computed(() => aiResult.value?.results ?? items.value)

function badgeClass(status) {
  return { Available: 'available', 'In Use': 'inuse', Repair: 'repair' }[status] || ''
}

onMounted(load)
</script>

<template>
  <div class="container">
    <div class="spread" style="margin-bottom: 18px">
      <h1>Equipment</h1>
      <span class="muted">{{ items.length }} items</span>
    </div>

    <!-- AI semantic search -->
    <div class="card ai-card">
      <div class="spread">
        <h2>🔎 Ask for what you need</h2>
        <span class="muted tag">{{ store.aiEnabled ? 'Claude' : 'fallback' }}</span>
      </div>
      <div class="row">
        <input
          v-model="aiQuery"
          class="grow"
          placeholder="e.g. something to test a mobile app on"
          @keyup.enter="runSearch"
        />
        <button class="primary" :disabled="aiSearching" @click="runSearch">
          {{ aiSearching ? '…' : 'Search' }}
        </button>
        <button v-if="aiResult" class="ghost" @click="clearSearch">Clear</button>
      </div>
      <p v-if="aiResult" class="muted explain">
        {{ aiResult.explanation }} ({{ aiResult.results.length }} matches)
      </p>
    </div>

    <!-- Filters -->
    <div class="card filters">
      <div class="row wrap">
        <input v-model="search" placeholder="Search by name…" @keyup.enter="load" />
        <select v-model="statusFilter" @change="load">
          <option value="">All statuses</option>
          <option>Available</option>
          <option>In Use</option>
          <option>Repair</option>
        </select>
        <select v-model="brandFilter" @change="load">
          <option value="">All brands</option>
          <option v-for="b in brands" :key="b">{{ b }}</option>
        </select>
        <button class="ghost" @click="load">Apply</button>
        <button class="ghost" @click="runAudit" :disabled="auditing">
          {{ auditing ? 'Auditing…' : '🩺 Run AI audit' }}
        </button>
      </div>
    </div>

    <!-- Auditor results -->
    <div v-if="audit" class="card audit">
      <div class="spread">
        <h2>AI Inventory Audit</h2>
        <span class="muted tag">{{ audit.source }}</span>
      </div>
      <p v-if="!audit.findings.length" class="muted">No issues found. 🎉</p>
      <ul v-else class="findings">
        <li v-for="(f, idx) in audit.findings" :key="idx">
          <span :class="`severity-${f.severity}`">[{{ f.severity }}]</span>
          <strong>{{ f.name }}</strong> — {{ f.issue }}
          <span class="muted">→ {{ f.recommendation }}</span>
        </li>
      </ul>
    </div>

    <!-- Table -->
    <div class="card">
      <table>
        <thead>
          <tr>
            <th class="sortable" @click="setSort('name')">Name</th>
            <th class="sortable" @click="setSort('brand')">Brand</th>
            <th class="sortable" @click="setSort('purchase_date')">Purchased</th>
            <th class="sortable" @click="setSort('status')">Status</th>
            <th>Holder</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in displayed" :key="item.id">
            <td>
              {{ item.name }}
              <div v-if="item.data_flag" class="flag" :title="item.data_flag">⚠ data flag</div>
            </td>
            <td>{{ item.brand || '—' }}</td>
            <td>{{ item.purchase_date || '—' }}</td>
            <td><span class="badge" :class="badgeClass(item.status)">{{ item.status }}</span></td>
            <td class="muted">{{ item.assigned_to || '—' }}</td>
            <td class="actions">
              <button
                v-if="item.status === 'Available'"
                class="primary"
                @click="rent(item)"
              >
                Rent
              </button>
              <button
                v-else-if="item.status === 'In Use'"
                @click="returnItem(item)"
              >
                Return
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="loading" class="muted pad">Loading…</p>
      <p v-else-if="!displayed.length" class="muted pad">No equipment matches.</p>
    </div>
  </div>
</template>

<style scoped>
.ai-card {
  margin-bottom: 14px;
}
.grow {
  flex: 1;
}
.tag {
  font-size: 12px;
  border: 1px solid var(--border);
  padding: 2px 8px;
  border-radius: 999px;
}
.explain {
  margin: 10px 0 0;
  font-size: 13px;
}
.filters {
  margin-bottom: 14px;
}
.wrap {
  flex-wrap: wrap;
}
.audit {
  margin-bottom: 14px;
}
.findings {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.findings li {
  line-height: 1.5;
}
.actions {
  text-align: right;
}
.pad {
  padding: 14px 4px 4px;
}
</style>
