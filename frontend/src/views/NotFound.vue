<template>
  <div class="not-found-container">
    <Card class="not-found-card">
      <template #header>
        <div class="not-found-icon">
          <i class="pi pi-map-marker not-found-marker"></i>
          <i class="pi pi-question-circle not-found-question"></i>
        </div>
      </template>
      <template #title>
        <h1 class="not-found-title">Page Not Found</h1>
      </template>
      <template #content>
        <div class="not-found-content">
          <p class="not-found-message">
            Oops! It seems you've wandered to a location that doesn't exist.
          </p>
          <div class="not-found-actions">
            <Button
              label="Go Home"
              icon="pi pi-home"
              @click="$router.push('/')"
              class="p-button-rounded p-button-primary"
            />
            <Button
              label="Find Meetings"
              icon="pi pi-search"
              @click="$router.push('/meetings/find')"
              class="p-button-rounded p-button-outlined"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--surface-ground);
  padding: 2rem;
}

.not-found-card {
  max-width: 500px;
  width: 100%;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.not-found-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 150px;
  position: relative;
}

.not-found-marker {
  font-size: 5rem;
  color: var(--primary-color);
}

.not-found-question {
  position: absolute;
  font-size: 3rem;
  color: var(--primary-color-text);
  background-color: var(--primary-color);
  border-radius: 50%;
  padding: 0.5rem;
  right: 50%;
  transform: translateX(3rem);
}

.not-found-title {
  color: var(--primary-color);
  margin: 0;
}

.not-found-content {
  padding: 1rem 0;
}

.not-found-message {
  margin-bottom: 2rem;
  font-size: 1.2rem;
  color: var(--text-color-secondary);
}

.not-found-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

@media (max-width: 576px) {
  .not-found-actions {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>