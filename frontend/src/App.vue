<template>
  <div class="app-container">
    <header v-if="isAuthenticated">
      <Menubar :model="menuItems" class="navbar">
        <template #start>
          <div class="logo-container" @click="$router.push('/')" style="cursor: pointer;">
            <img src="@/assets/logo.png" alt="StepIn Logo" height="40" />
            <h1 class="app-title">StepIn</h1>
          </div>
        </template>
        <template #end>
          <div class="user-menu">
            <!-- Chat icon - always visible but colored/animated only when in a meeting -->
            <div class="status-container" v-if="joinedMeeting">
              <Badge value="Active Meeting" severity="success" />
              <span class="meeting-name">{{ joinedMeeting.title }}</span>
            </div>
            <Button 
              icon="pi pi-comments" 
              :class="[
                'p-button-rounded p-button-text',
                joinedMeeting ? 'p-button-success chat-indicator' : 'p-button-secondary'
              ]" 
              v-tooltip="joinedMeeting ? 'Go to active meeting chat' : 'No active meeting'"
              @click="joinedMeeting ? $router.push('/chat') : null"
              :disabled="!joinedMeeting"
            />
            
            <div 
              class="profile-container" 
              @click="$router.push('/profile')"
              v-tooltip="'View Profile'"
            >
              <Avatar 
                :label="getUserInitials()" 
                shape="circle" 
                :style="{ backgroundColor: getUserColor() }" 
                class="user-avatar"
              />
              <span class="user-name">{{ currentUser?.name || 'User' }}</span>
            </div>
            <Button icon="pi pi-sign-out" class="p-button-rounded p-button-text" @click="logout" v-tooltip="'Logout'" />
          </div>
        </template>
      </Menubar>
    </header>
    
    <main>
      <div v-if="isLoading" class="loading-overlay">
        <ProgressSpinner />
      </div>
      <keep-alive>
        <router-view v-if="!isLoading" />
      </keep-alive>
    </main>
    
    <footer v-if="isAuthenticated">
      <div class="footer-content">
        <div class="copyright">
          © {{ new Date().getFullYear() }} StepIn - Physical Meeting Platform
        </div>
      </div>
    </footer>
  </div>
  
  <Toast />
  <ConfirmDialog />
</template>

<script>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

export default {
  name: 'App',
  setup() {
    const store = useStore();
    const router = useRouter();
    
    const isAuthenticated = computed(() => store.getters.isAuthenticated);
    const currentUser = computed(() => store.getters.currentUser);
    const isLoading = computed(() => store.getters.isLoading);
    const joinedMeeting = computed(() => store.getters.joinedMeeting);
    
    // Navigation menu
    const goTo = (path) => {
      router.push(path);
    };

    const menuItems = [
      {
        label: 'Dashboard',
        icon: 'pi pi-fw pi-home',
        command: () => goTo('/')
      },
      {
        label: 'Meetings',
        icon: 'pi pi-fw pi-calendar',
        items: [
          {
            label: 'All Meetings',
            icon: 'pi pi-fw pi-list',
            command: () => goTo('/meetings')
          },
          {
            label: 'Find Nearby',
            icon: 'pi pi-fw pi-search',
            command: () => goTo('/meetings/find')
          },
          {
            label: 'Create Meeting',
            icon: 'pi pi-fw pi-plus',
            command: () => goTo('/meetings/create')
          }
        ]
      }
    ];
    
    // Check auth on load
    store.dispatch('checkAuth');
    
    // Helper functions
    const getUserInitials = () => {
      if (!currentUser.value || !currentUser.value.name) {
        return '?';
      }
      
      const nameParts = currentUser.value.name.split(' ');
      if (nameParts.length === 1) {
        return nameParts[0].substring(0, 2).toUpperCase();
      }
      
      return (nameParts[0].charAt(0) + nameParts[1].charAt(0)).toUpperCase();
    };
    
    const getUserColor = () => {
      if (!currentUser.value || !currentUser.value.email) {
        return 'var(--primary-color)';
      }
      
      // Generate consistent color based on email
      let hash = 0;
      const email = currentUser.value.email;
      for (let i = 0; i < email.length; i++) {
        hash = email.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      const hue = hash % 360;
      return `hsl(${hue}, 70%, 60%)`;
    };
    
    const logout = () => {
      store.dispatch('logout');
      router.push('/login');
    };
    
    const openChat = () => {
      router.push('/chat');
    };
    
    return {
      isAuthenticated,
      currentUser,
      isLoading,
      joinedMeeting,
      menuItems,
      getUserInitials,
      getUserColor,
      logout,
      openChat
    };
  }
};
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: var(--font-family);
  background-color: var(--surface-ground);
  color: var(--text-color);
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.logo-container {
  display: flex;
  align-items: center;
}

.app-title {
  margin-left: 10px;
  font-size: 1.5rem;
  color: var(--primary-color);
  margin-top: 0;
  margin-bottom: 0;
}

main {
  flex: 1;
  padding: 20px;
  position: relative;
}

footer {
  padding: 15px 20px;
  background-color: var(--surface-card);
  border-top: 1px solid var(--surface-border);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-container {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.5rem;
  border-radius: 30px;
  background-color: rgba(76, 175, 80, 0.1);
  border: 1px solid var(--surface-border);
  margin-right: 5px;
}

.meeting-name {
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9rem;
}

.profile-container {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 30px;
  background-color: transparent;
  border: 1px solid var(--surface-border);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  margin-right: 0.5rem;
}

.profile-container:hover {
  background-color: var(--surface-ground);
  transform: translateY(-2px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.08);
}

.user-avatar {
  margin-right: 8px;
}

.user-name {
  margin-right: 10px;
  font-weight: 600;
}

.meeting-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-indicator {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
  }
}

/* Responsive Adjustments */
/* Navbar styling */
.p-menubar {
  padding: 0.5rem 1rem;
}

.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-link {
  padding: 0.75rem 1rem;
}

.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-link:focus,
.p-menubar .p-menubar-root-list > .p-menuitem.p-highlight > .p-menuitem-link {
  background-color: var(--surface-hover);
}

@media (max-width: 768px) {
  .user-name {
    display: none;
  }
  
  .meeting-name {
    display: none;
  }
  
  .status-container {
    padding: 0.3rem;
  }
  
  main {
    padding: 10px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
}
</style>