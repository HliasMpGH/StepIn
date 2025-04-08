<template>
  <div class="profile-page">
    <h1 class="profile-title">My Profile</h1>
    
    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>
    
    <div v-else class="profile-layout">
      <div class="profile-main">
        <div class="profile-avatar">
          <Avatar 
            :label="getInitials()" 
            size="xlarge" 
            shape="circle" 
            :style="{ backgroundColor: getAvatarColor() }" 
          />
        </div>

        <div class="profile-info">
          <div class="info-row">
            <div class="info-label">Email</div>
            <div class="info-value">{{ user.email }}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">Name</div>
            <div class="info-value">{{ user.name }}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">Age</div>
            <div class="info-value">{{ user.age || 'Not specified' }}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">Gender</div>
            <div class="info-value">{{ formatGender(user.gender) }}</div>
          </div>
        </div>
      </div>
      
      <div class="profile-actions">
        <Button 
          label="Edit Profile" 
          icon="pi pi-user-edit" 
          @click="editProfile" 
          class="p-button-primary"
        />
        
        <Button 
          label="Logout" 
          icon="pi pi-sign-out" 
          @click="logout" 
          class="p-button-danger p-button-outlined"
        />
      </div>
    </div>
  </div>

    <Dialog
      v-model:visible="editDialogVisible"
      modal
      header="Edit Profile"
      :style="{ width: '450px' }"
      :closable="false"
    >
      <div class="edit-form">
        <div class="p-field">
          <label for="edit-name">Name</label>
          <InputText id="edit-name" v-model="editForm.name" class="p-inputtext-lg" />
        </div>

        <div class="p-field">
          <label for="edit-age">Age</label>
          <InputNumber id="edit-age" v-model="editForm.age" :min="15" :max="120" class="p-inputtext-lg" />
        </div>

        <div class="p-field">
          <label for="edit-gender">Gender</label>
          <Dropdown
            id="edit-gender"
            v-model="editForm.gender"
            :options="genderOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select Gender"
            class="p-inputtext-lg w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Cancel"
          icon="pi pi-times"
          @click="editDialogVisible = false"
          class="p-button-text"
        />
        <Button
          label="Save"
          icon="pi pi-check"
          @click="saveProfile"
          :loading="saving"
          class="p-button-success"
        />
      </template>
    </Dialog>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

export default {
  name: 'UserProfile',
  setup() {
    const store = useStore();
    const router = useRouter();
    const toast = useToast();

    const loading = ref(true);

    // Edit profile
    const editDialogVisible = ref(false);
    const editForm = ref({
      name: '',
      age: null,
      gender: null
    });
    const saving = ref(false);

    const genderOptions = [
      { label: 'Male', value: 'male' },
      { label: 'Female', value: 'female' },
      { label: 'Other', value: 'other' },
      { label: 'Prefer not to say', value: 'undisclosed' }
    ];

    const user = computed(() => store.getters.currentUser || {});

    onMounted(async () => {
      if (!store.getters.isAuthenticated) {
        router.push('/login');
        return;
      }

      try {
        // Fetch user data if needed
        await fetchUserData();
      } catch (error) {
        console.error('Error loading profile:', error);
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load profile data',
          life: 3000
        });
      } finally {
        loading.value = false;
      }
    });

    const fetchUserData = async () => {
      // This function would call an API to get the latest user data
      // For now, we'll use what's in the store
      return new Promise(resolve => {
        // Simulate API delay
        setTimeout(resolve, 800);
      });
    };


    const getInitials = () => {
      if (!user.value.name) return '??';

      const nameParts = user.value.name.split(' ');
      if (nameParts.length === 1) {
        return nameParts[0].substring(0, 2).toUpperCase();
      }

      return (nameParts[0].charAt(0) + nameParts[1].charAt(0)).toUpperCase();
    };

    const getAvatarColor = () => {
      // Generate a consistent color based on email
      if (!user.value.email) return 'var(--primary-color)';

      let hash = 0;
      for (let i = 0; i < user.value.email.length; i++) {
        hash = user.value.email.charCodeAt(i) + ((hash << 5) - hash);
      }

      const hue = hash % 360;
      return `hsl(${hue}, 70%, 60%)`;
    };

    const formatGender = (gender) => {
      if (!gender) return 'Not specified';

      const option = genderOptions.find(opt => opt.value === gender);
      return option ? option.label : 'Not specified';
    };

    const editProfile = () => {
      // Copy current user data to edit form
      editForm.value = {
        name: user.value.name || '',
        age: user.value.age || null,
        gender: user.value.gender || null
      };

      editDialogVisible.value = true;
    };

    const saveProfile = async () => {
      if (!editForm.value.name) {
        toast.add({
          severity: 'warn',
          summary: 'Warning',
          detail: 'Name is required',
          life: 3000
        });
        return;
      }

      saving.value = true;

      try {
        // Update user in store (in a real app this would be an API call)
        const updatedUser = {
          ...user.value,
          name: editForm.value.name,
          age: editForm.value.age,
          gender: editForm.value.gender
        };

        // Update user in localStorage
        localStorage.setItem('user', JSON.stringify(updatedUser));

        // Update user in store
        store.commit('SET_USER', updatedUser);

        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Profile updated successfully',
          life: 3000
        });

        editDialogVisible.value = false;
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update profile',
          life: 3000
        });
      } finally {
        saving.value = false;
      }
    };

    const logout = () => {
      store.dispatch('logout');
      router.push('/login');
      toast.add({
        severity: 'info',
        summary: 'Logged Out',
        detail: 'You have been logged out successfully',
        life: 3000
      });
    };

    return {
      loading,
      user,
      editDialogVisible,
      editForm,
      genderOptions,
      saving,
      getInitials,
      getAvatarColor,
      formatGender,
      editProfile,
      saveProfile,
      logout
    };
  }
};
</script>

<style scoped>
.profile-page {
  margin: 3rem auto;
  padding: 0 2rem;
  max-width: 1000px;
}

.profile-title {
  color: var(--primary-color);
  font-size: 2.5rem;
  text-align: center;
  margin-bottom: 3rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.profile-layout {
  display: flex;
  flex-direction: column;
  gap: 3rem;
  background-color: var(--surface-card);
  padding: 3rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.profile-main {
  display: flex;
  align-items: flex-start;
  gap: 4rem;
}

.profile-avatar {
  display: flex;
  justify-content: center;
  align-items: center;
  transform: scale(1.7);
  padding-top: 1rem;
}

.profile-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--surface-200);
  padding: 1rem 0;
  width: 100%;
}

.info-label {
  flex: 0 0 150px;
  font-weight: 600;
  color: var(--text-color-secondary);
  font-size: 1.2rem;
}

.info-value {
  flex: 1;
  color: var(--text-color);
  font-size: 1.2rem;
  font-weight: 500;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-200);
}

.profile-actions .p-button {
  font-size: 1.1rem;
  padding: 0.5rem 1.5rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem 0;
}

.p-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.p-field label {
  font-weight: 600;
}

.w-full {
  width: 100%;
}

@media (max-width: 768px) {
  .profile-page {
    padding: 1rem;
    margin: 1rem auto;
  }

  .profile-title {
    font-size: 2rem;
    margin-bottom: 2rem;
  }

  .profile-layout {
    padding: 1.5rem;
  }

  .profile-main {
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }

  .profile-info {
    width: 100%;
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 1rem 0;
  }

  .info-label {
    flex: 0 0 auto;
  }

  .profile-actions {
    flex-direction: column;
    width: 100%;
  }

  .profile-actions .p-button {
    width: 100%;
  }
}
</style>