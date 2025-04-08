<template>
  <div class="register-container">
    <Card class="register-card">
      <template #title>
        <div class="register-header">
          <h1 class="register-title">Create Account</h1>
        </div>
      </template>
      <template #content>
        <form @submit.prevent="register">
          <div class="p-fluid">
            <div class="field">
              <label for="email">Email</label>
              <InputText 
                id="email" 
                v-model="user.email" 
                type="email" 
                required 
                :class="{'p-invalid': submitted && !user.email}"
              />
              <small v-if="submitted && !user.email" class="p-error">Email is required</small>
            </div>
            
            <div class="field">
              <label for="name">Full Name</label>
              <InputText 
                id="name" 
                v-model="user.name" 
                required 
                :class="{'p-invalid': submitted && !user.name}"
              />
              <small v-if="submitted && !user.name" class="p-error">Name is required</small>
            </div>
            
            <div class="field">
              <label for="age">Age</label>
              <InputNumber 
                id="age" 
                v-model="user.age" 
                :min="15" 
                :max="120"
              />
            </div>
            
            <div class="field">
              <label for="gender">Gender</label>
              <Dropdown 
                id="gender" 
                v-model="user.gender" 
                :options="genderOptions" 
                optionLabel="label" 
                optionValue="value"
                placeholder="Select Gender"
              />
            </div>
            
            <div class="field mt-4">
              <Message v-if="error" severity="error">{{ error }}</Message>
            </div>
            
            <div class="field mt-4">
              <Button 
                type="submit" 
                label="Register" 
                icon="pi pi-user-plus" 
                :loading="loading"
                class="p-button-raised p-button-rounded"
              />
            </div>
            
            <div class="field mt-2 text-center">
              <span>Already have an account? </span>
              <router-link to="/login">Login</router-link>
            </div>
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>

<script>
export default {
  name: 'Register',
  data() {
    return {
      user: {
        email: '',
        name: '',
        age: null,
        gender: null
      },
      genderOptions: [
        { label: 'Male', value: 'male' },
        { label: 'Female', value: 'female' },
        { label: 'Other', value: 'other' },
        { label: 'Prefer not to say', value: 'undisclosed' }
      ],
      submitted: false,
      loading: false,
      error: ''
    }
  },
  methods: {
    async register() {
      this.submitted = true
      
      if (!this.user.email || !this.user.name) {
        return
      }
      
      try {
        this.loading = true
        this.error = ''
        
        // Call API to create user
        const result = await this.$store.dispatch('createUser', this.user)
        
        if (result.success) {
          this.$toast.add({
            severity: 'success',
            summary: 'Registration Complete',
            detail: 'Your account has been created successfully',
            life: 3000
          })
          
          // Redirect to dashboard
          this.$router.push('/')
        }
      } catch (err) {
        this.error = err.response?.data?.error || 'Error creating account. Please try again.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--surface-ground);
}

.register-card {
  width: 100%;
  max-width: 500px;
  margin-bottom: 2rem;
  box-shadow: 0 2px 1px -1px rgba(0,0,0,.2), 0 1px 1px 0 rgba(0,0,0,.14), 0 1px 3px 0 rgba(0,0,0,.12);
}

.register-header {
  text-align: center;
  padding: 1rem 0;
}

.register-title {
  color: var(--primary-color);
}

.text-center {
  text-align: center;
}
</style>