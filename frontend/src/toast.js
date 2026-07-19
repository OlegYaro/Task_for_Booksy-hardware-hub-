import { reactive } from 'vue'

export const toast = reactive({
  message: '',
  kind: 'ok', // 'ok' | 'err'
  _timer: null,

  show(message, kind = 'ok') {
    this.message = message
    this.kind = kind
    clearTimeout(this._timer)
    this._timer = setTimeout(() => (this.message = ''), 3000)
  },

  error(err) {
    this.show(err?.message || String(err), 'err')
  },
})
