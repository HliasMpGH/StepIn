<template>
  <div class="login-container">
    <Card class="login-card">
      <template #title>
        <div class="login-header">
          <img src="@/assets/logo.png" alt="StepIn Logo" class="stepin-logo" />
          <h1 class="login-title">Welcome to StepIn</h1>
        </div>
      </template>
      <template #content>
        <form @submit.prevent="login">
          <div class="p-fluid">
            <div class="field">
              <label for="email">Email</label>
              <InputText
                id="email"
                v-model="email"
                type="email"
                required
                :class="{'p-invalid': submitted && !email}"
              />
              <small v-if="submitted && !email" class="p-error">Email is required</small>
            </div>

            <div class="field mt-4">
              <Message v-if="error" severity="error">{{ error }}</Message>
            </div>

            <div class="field mt-4">
              <Button
                type="submit"
                label="Log In"
                icon="pi pi-sign-in"
                :loading="loading"
                class="p-button-raised p-button-rounded"
              />
            </div>

            <div class="field mt-2 text-center">
              <span>Don't have an account? </span>
              <router-link to="/register">Register</router-link>
            </div>
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      email: '',
      submitted: false,
      loading: false,
      error: ''
    }
  },
  methods: {
    async login() {
      this.submitted = true
      this.loading = true
      this.error = ''

      if (!this.email) {
        this.loading = false
        return
      }

      try {
        const response = await this.$store.dispatch('getUser', this.email)

        // User exists, proceed with login
        await this.$store.dispatch('login', response)

        // Redirect after login
        const redirectPath = this.$route.query.redirect || '/'
        this.$router.push(redirectPath)

        this.$toast.add({
          severity: 'success',
          summary: 'Welcome back!',
          detail: `You are now logged in as ${response.name}`,
          life: 3000
        })
      } catch (err) {
        // user does not exist or internal error
        const errorMessage = err.response?.data?.detail ||
                            err.message || 'Error logging in.';

        this.error = errorMessage
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--surface-ground);
}

.login-card {
  width: 100%;
  max-width: 450px;
  margin-bottom: 2rem;
  box-shadow: 0 2px 1px -1px rgba(0,0,0,.2), 0 1px 1px 0 rgba(0,0,0,.14), 0 1px 3px 0 rgba(0,0,0,.12);
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0;
}

.login-title {
  color: var(--primary-color);
  margin-top: 1rem;
}
.stepin-logo {
  height: 230px;
  width: auto;
  background: transparent;
  margin: 0;
  padding: 0;
  box-shadow: none;
  border: none;
}
.text-center {
  text-align: center;
}
</style>