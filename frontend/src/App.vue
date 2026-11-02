<script setup lang="ts">
import { onMounted, ref } from 'vue'
const status = ref('Проверяем соединение…')
const loading = ref(false)
async function check() {
  loading.value = true
  try {
    const response = await fetch('/api/health/ready', { signal: AbortSignal.timeout(5000) })
    if (!response.ok) throw new Error('unavailable')
    status.value = 'Backend и база данных доступны'
  } catch {
    status.value = 'Сервис временно недоступен. Повторите проверку.'
  } finally { loading.value = false }
}
onMounted(check)
</script>

<template>
  <main>
    <p class="brand">TECH TRANSPORT</p>
    <h1>Техника для вашей задачи</h1>
    <p>Здесь появится карта доступной техники Беларуси и контакты владельцев.</p>
    <section aria-label="Состояние сервиса">
      <h2>Основа проекта готова</h2>
      <p role="status">{{ status }}</p>
      <button :disabled="loading" @click="check">{{ loading ? 'Проверяем…' : 'Проверить соединение' }}</button>
    </section>
  </main>
</template>

<style>
:root { font-family: system-ui, sans-serif; color: #16332c; background: #f2f5f1; }
body { margin: 0; }
main { max-width: 820px; margin: 10vh auto; padding: 24px; }
.brand { font-size: 14px; letter-spacing: .15em; font-weight: 700; }
h1 { font-size: clamp(32px, 6vw, 56px); line-height: 1.1; }
p { line-height: 1.6; }
section { margin-top: 40px; padding: 24px; background: white; border-radius: 16px; }
h2 { margin-top: 0; }
button { background: #205946; color: white; border: 0; border-radius: 8px; padding: 12px 18px; font: inherit; cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
</style>
