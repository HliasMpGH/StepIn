<template>
  <div class="meetings-list-container">
    <div class="header">
      <h1>My Meetings</h1>
      <Button 
        label="Create Meeting" 
        icon="pi pi-plus" 
        class="p-button-rounded p-button-success" 
        @click="navigateToCreate"
      />
    </div>

    <div class="card">
      <TabView>
        <TabPanel header="Active Meetings">
          <div v-if="loading" class="loading-container">
            <ProgressSpinner />
          </div>
          <div v-else-if="activeMeetings.length === 0" class="no-meetings">
            <i class="pi pi-calendar-times no-meetings-icon"></i>
            <p>No active meetings found</p>
            <Button 
              label="Find Nearby Meetings" 
              icon="pi pi-search" 
              class="p-button-rounded p-button-info" 
              @click="navigateToFind"
            />
          </div>
          <div v-else class="meetings-grid">
            <div v-for="meeting in activeMeetings" :key="meeting.meeting_id" class="meeting-card">
              <Card>
                <template #header>
                  <div class="meeting-header">
                    <Badge value="Active" severity="success" />
                  </div>
                </template>
                <template #title>
                  <div class="meeting-title">{{ meeting.title }}</div>
                </template>
                <template #content>
                  <div class="meeting-info">
                    <p>{{ meeting.description }}</p>
                    <div class="meeting-details">
                      <div class="detail-item">
                        <i class="pi pi-calendar"></i>
                        <span>{{ formatDate(meeting.t1) }} - {{ formatDate(meeting.t2) }}</span>
                      </div>
                      <div class="detail-item">
                        <i class="pi pi-users"></i>
                        <span>{{ meeting.participants.split(',').length }} participants</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div class="meeting-actions">
                    <Button 
                      label="Join" 
                      icon="pi pi-sign-in" 
                      @click="joinMeeting(meeting.meeting_id)" 
                      class="p-button-sm"
                    />
                    <Button 
                      label="View" 
                      icon="pi pi-info-circle" 
                      @click="viewMeeting(meeting.meeting_id)" 
                      class="p-button-sm p-button-outlined"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </TabPanel>
        
        <TabPanel header="Upcoming Meetings">
          <div v-if="loading" class="loading-container">
            <ProgressSpinner />
          </div>
          <div v-else-if="upcomingMeetings.length === 0" class="no-meetings">
            <i class="pi pi-calendar-plus no-meetings-icon"></i>
            <p>No upcoming meetings found</p>
            <Button 
              label="Create a Meeting" 
              icon="pi pi-plus" 
              class="p-button-rounded p-button-success" 
              @click="navigateToCreate"
            />
          </div>
          <div v-else class="meetings-grid">
            <div v-for="meeting in upcomingMeetings" :key="meeting.meeting_id" class="meeting-card">
              <Card>
                <template #header>
                  <div class="meeting-header">
                    <Badge value="Upcoming" severity="info" />
                  </div>
                </template>
                <template #title>
                  <div class="meeting-title">{{ meeting.title }}</div>
                </template>
                <template #content>
                  <div class="meeting-info">
                    <p>{{ meeting.description }}</p>
                    <div class="meeting-details">
                      <div class="detail-item">
                        <i class="pi pi-calendar"></i>
                        <span>{{ formatDate(meeting.t1) }} - {{ formatDate(meeting.t2) }}</span>
                      </div>
                      <div class="detail-item">
                        <i class="pi pi-users"></i>
                        <span>{{ meeting.participants.split(',').length }} participants</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div class="meeting-actions">
                    <Button 
                      label="View" 
                      icon="pi pi-info-circle" 
                      @click="viewMeeting(meeting.meeting_id)" 
                      class="p-button-sm p-button-outlined"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </TabPanel>
      </TabView>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

export default {
  name: 'MeetingsList',
  activated() {
    // Call the setup hook's onActivated method
    if (this.onActivated) {
      this.onActivated();
    }
  },
  setup() {
    const store = useStore();
    const router = useRouter();
    const toast = useToast();
    const loading = ref(false);
    const activeMeetings = ref([]);
    const upcomingMeetings = ref([]);
    
    const isAuthenticated = computed(() => store.getters.isAuthenticated);
    
    // Add a refresher that runs when the component is activated (comes back into view)
    const refreshOnActivate = ref(true);
    
    onMounted(async () => {
      if (!isAuthenticated.value) {
        router.push('/login');
        return;
      }
      
      await fetchMeetings();
      
      // Listen for route changes - when returning to this page, refresh data
      router.beforeEach((to, from, next) => {
        if (to.path === '/meetings' && from.path === '/meetings/create') {
          refreshOnActivate.value = true;
        }
        next();
      });
    });
    
    // Add an activate hook (runs when component becomes visible again)
    const onActivated = async () => {
      if (refreshOnActivate.value) {
        console.log('Component activated - refreshing meetings');
        await fetchMeetings();
        refreshOnActivate.value = false;
      }
    };
    
    const fetchMeetings = async () => {
      loading.value = true;
      try {
        console.log('Fetching meetings...');
        // Get meetings from API
        const response = await store.dispatch('getActiveMeetings');
        console.log('Meetings response:', response);
        
        // Separate active from upcoming meetings
        const now = new Date();
        
        activeMeetings.value = response.filter(meeting => {
          const startTime = new Date(meeting.t1);
          const endTime = new Date(meeting.t2);
          return startTime <= now && endTime >= now;
        });
        
        upcomingMeetings.value = response.filter(meeting => {
          const startTime = new Date(meeting.t1);
          return startTime > now;
        });
        
        console.log('Active meetings:', activeMeetings.value);
        console.log('Upcoming meetings:', upcomingMeetings.value);
      } catch (error) {
        console.error('Error fetching meetings:', error);
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to fetch meetings',
          life: 3000
        });
      } finally {
        loading.value = false;
      }
    };
    
    const joinMeeting = async (meetingId) => {
      try {
        const result = await store.dispatch('joinMeeting', meetingId);
        if (result.success) {
          toast.add({
            severity: 'success',
            summary: 'Success',
            detail: 'You have joined the meeting',
            life: 3000
          });
          router.push('/chat');
        }
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to join meeting',
          life: 3000
        });
      }
    };
    
    const viewMeeting = (meetingId) => {
      router.push(`/meetings/${meetingId}`);
    };
    
    const navigateToCreate = () => {
      router.push('/meetings/create');
    };
    
    const navigateToFind = () => {
      router.push('/meetings/find');
    };
    
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString();
    };
    
    return {
      loading,
      activeMeetings,
      upcomingMeetings,
      joinMeeting,
      viewMeeting,
      navigateToCreate,
      navigateToFind,
      formatDate,
      onActivated
    };
  }
};
</script>

<style scoped>
.meetings-list-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0;
  color: var(--primary-color);
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 3rem;
}

.no-meetings {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
  text-align: center;
}

.no-meetings-icon {
  font-size: 3rem;
  color: var(--text-color-secondary);
  margin-bottom: 1rem;
}

.meetings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.meeting-card {
  height: 100%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.meeting-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.meeting-header {
  padding: 1rem;
  display: flex;
  justify-content: flex-end;
}

.meeting-title {
  font-weight: 600;
  font-size: 1.2rem;
}

.meeting-info {
  margin-bottom: 1rem;
}

.meeting-details {
  margin-top: 1rem;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.detail-item i {
  margin-right: 0.5rem;
  color: var(--primary-color);
}

.meeting-actions {
  display: flex;
  justify-content: space-between;
}

@media (max-width: 768px) {
  .meetings-grid {
    grid-template-columns: 1fr;
  }
  
  .header {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>