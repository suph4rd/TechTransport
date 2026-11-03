<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
interface User { id: number; phone: string; display_name: string; role: string }
const user = ref<User | null>(null)
const csrfToken = ref('login')
const phone = ref('')
const code = ref('')
const displayName = ref('')
const codeSent = ref(false)
const busy = ref(false)
const message = ref('')
const error = ref('')
const ready = ref(false)
const retryAt = ref(0)
const secondsLeft = ref(0)
let timer: ReturnType<typeof setInterval> | undefined
async function api(path: string, method = 'GET', body?: unknown) {
  const response = await fetch(`/api/auth/${path}`, {
    method, credentials: 'same-origin', signal: AbortSignal.timeout(10000),
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken.value },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  const data = response.status === 204 ? null : await response.json()
  if (!response.ok) {
    if (response.status === 401 || (response.status === 403 && data?.error?.message === 'Аккаунт отключён')) {
      user.value = null
      csrfToken.value = 'login'
    }
    throw new Error(data?.error?.message ?? 'Не удалось выполнить запрос')
  }
  return data
}
function setSession(data: { user: User; csrf_token: string }) {
  user.value = data.user
  displayName.value = data.user.display_name
  csrfToken.value = data.csrf_token
  code.value = ''
}
async function run(action: () => Promise<void>) {
  busy.value = true
  error.value = ''
  message.value = ''
  try { await action() }
  catch (e) { error.value = e instanceof Error ? e.message : 'Сервис недоступен. Повторите попытку.' }
  finally { busy.value = false }
}
async function sendCode() {
  await run(async () => {
    await api('code', 'POST', { phone: phone.value })
    codeSent.value = true
    retryAt.value = Date.now() + 60000
    secondsLeft.value = 60
    if (timer) clearInterval(timer)
    timer = setInterval(() => {
      secondsLeft.value = Math.max(0, Math.ceil((retryAt.value - Date.now()) / 1000))
      if (!secondsLeft.value) clearInterval(timer)
    }, 1000)
    message.value = 'Код отправлен. В локальной версии он находится в журнале backend. Срок действия — 5 минут.'
  })
}
async function verify() {
  await run(async () => {
    setSession(await api('verify', 'POST', { phone: phone.value, code: code.value }))
    message.value = 'Вы вошли в аккаунт'
  })
}
async function save() {
  await run(async () => {
    setSession(await api('me', 'PATCH', { display_name: displayName.value }))
    message.value = 'Имя сохранено'
  })
}
async function refresh() {
  await run(async () => {
    setSession(await api('refresh', 'POST'))
    message.value = 'Сессия обновлена на 7 дней'
  })
}
async function logout() {
  await run(async () => {
    await api('logout', 'POST')
    user.value = null
    csrfToken.value = 'login'
    codeSent.value = false
    code.value = ''
    message.value = 'Вы вышли из аккаунта'
  })
}
onUnmounted(() => { if (timer) clearInterval(timer) })
onMounted(async () => {
  try { setSession(await api('me')) }
  catch (e) {
    if (e instanceof Error && e.message !== 'Войдите в аккаунт') error.value = e.message
  } finally { ready.value = true }
})
</script>

<template>
  <main>
    <p class="brand">TECH TRANSPORT</p>
    <h1>Техника для вашей задачи</h1>
    <p>Поиск техники Беларуси и контакты владельцев.</p>
    <p v-if="!ready" role="status">Загружаем профиль…</p>
    <section v-else-if="!user" aria-labelledby="login-title">
      <h2 id="login-title">Вход по телефону</h2>
      <form @submit.prevent="sendCode">
        <label for="phone">Мобильный телефон Беларуси</label>
        <input id="phone" v-model="phone" type="tel" autocomplete="tel" placeholder="+375 29 123 45 67" maxlength="40" required :disabled="busy || codeSent" />
        <button type="submit" :disabled="busy || secondsLeft > 0">{{ secondsLeft ? `Повторить через ${secondsLeft} с` : codeSent ? 'Отправить код повторно' : 'Получить код' }}</button>
        <button v-if="codeSent" class="secondary" type="button" :disabled="busy" @click="codeSent = false; code = ''">Другой номер</button>
      </form>
      <form v-if="codeSent" @submit.prevent="verify">
        <label for="code">Код из 6 цифр</label>
        <input id="code" v-model="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required :disabled="busy" />
        <button type="submit" :disabled="busy">Войти</button>
      </form>
      <p class="hint">Локальная SMS-заглушка: код выводится в журнал backend.</p>
    </section>
    <section v-else aria-labelledby="profile-title">
      <h2 id="profile-title">Мой профиль</h2>
      <p>{{ user.phone }}</p>
      <p v-if="user.role === 'admin'">Администратор</p>
      <form @submit.prevent="save">
        <label for="name">Отображаемое имя</label>
        <input id="name" v-model="displayName" autocomplete="name" maxlength="100" required :disabled="busy" />
        <button type="submit" :disabled="busy">Сохранить имя</button>
      </form>
      <div class="actions">
        <button class="secondary" :disabled="busy" @click="refresh">Обновить сессию</button>
        <button class="secondary" :disabled="busy" @click="logout">Выйти</button>
      </div>
    </section>
    <p v-if="message" role="status">{{ message }}</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
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

<style>
form { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; margin-top: 24px; }
input { box-sizing: border-box; width: 100%; max-width: 400px; padding: 12px; border: 1px solid #79958a; border-radius: 8px; font: inherit; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 24px; }
.secondary { background: #e2ede7; color: #16332c; }
.error { color: #a02222; }
.hint { color: #52675e; font-size: 14px; }
button:focus-visible, input:focus-visible { outline: 3px solid #c48b22; outline-offset: 3px; }
</style>
