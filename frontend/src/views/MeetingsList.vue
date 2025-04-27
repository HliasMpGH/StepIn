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
              <Card class="custom-card">
                <template #header>
                  <div class="meeting-header">
                    <h3 class="meeting-title">{{ meeting.title }}</h3>
                    <Badge value="Active" severity="success" />
                  </div>
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
                        <span>{{ meeting.participants.length }} participants</span>
                      </div>
                      <div class="detail-item">
                        <i class="pi pi-map-marker"></i>
                        <span>Lat: {{ meeting.lat.toFixed(4) }}, Long: {{ meeting.long.toFixed(4) }}</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div class="meeting-actions">
                    <Button
                      label="View Details"
                      icon="pi pi-info-circle"
                      @click="viewMeeting(meeting.meeting_id)"
                      class="p-button p-button-info p-button-outlined"
                    />
                    <Button
                      label="Join Meeting"
                      icon="pi pi-sign-in"
                      @click="joinMeeting(meeting.meeting_id)"
                      class="p-button p-button-success"
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
              <Card class="custom-card">
                <template #header>
                  <div class="meeting-header">
                    <h3 class="meeting-title">{{ meeting.title }}</h3>
                    <Badge value="Upcoming" severity="info" />
                  </div>
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
                        <span>{{ meeting.participants.length }} participants</span>
                      </div>
                      <div class="detail-item">
                        <i class="pi pi-map-marker"></i>
                        <span>Lat: {{ meeting.lat.toFixed(4) }}, Long: {{ meeting.long.toFixed(4) }}</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div class="meeting-actions">
                    <Button
                      label="View Details"
                      icon="pi pi-info-circle"
                      @click="viewMeeting(meeting.meeting_id)"
                      class="p-button p-button-info"
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

        let activeResponse = [];
        let upcomingResponse = [];

        try {
          activeResponse = await store.dispatch('getActiveMeetings', { forceRefresh: true });
          console.log('Active meetings response:', activeResponse);
        } catch (activeError) {
          console.error('Error fetching active meetings:', activeError);
          toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to fetch active meetings',
            life: 3000
          });
        }

        try {
          upcomingResponse = await store.dispatch('getUpcomingMeetings', { forceRefresh: true });
          console.log('Upcoming meetings response:', upcomingResponse);
        } catch (upcomingError) {
          console.error('Error fetching upcoming meetings:', upcomingError);
          toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to fetch upcoming meetings',
            life: 3000
          });
        }

        activeMeetings.value = activeResponse || [];
        upcomingMeetings.value = upcomingResponse || [];

        activeMeetings.value.sort((a, b) => new Date(a.t1) - new Date(b.t1));
        upcomingMeetings.value.sort((a, b) => new Date(a.t1) - new Date(b.t1));

      } catch (error) {
        console.error('General error in fetchMeetings:', error);
        activeMeetings.value = [];
        upcomingMeetings.value = [];
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
        const errorMessage = error.response?.data?.detail ||
                            error.message || 'Failed to join meeting';
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: errorMessage,
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
}

.custom-card {
  height: 100%;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  background-color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}


.custom-card :deep(.p-card-content) {
    flex-grow: 1;
}


.custom-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.meeting-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--surface-ground);
  border-bottom: 1px solid var(--surface-border);
}

.meeting-title {
  font-weight: 700;
  font-size: 1.3rem;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.meeting-info {
  color: var(--text-color);
}

.meeting-info p {
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.meeting-details {
  margin-top: 1.5rem;
  background-color: var(--surface-section);
  padding: 1rem;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 0.8rem;
  font-size: 1rem;
}

.detail-item i {
  margin-right: 0.8rem;
  color: var(--primary-color);
  font-size: 1.2rem;
}

.meeting-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.8rem;
  margin-top: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--surface-border);
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