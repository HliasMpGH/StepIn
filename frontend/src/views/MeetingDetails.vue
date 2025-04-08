<template>
  <div class="meeting-details-container">
    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>
    
    <div v-else-if="!meeting" class="not-found">
      <h2>Meeting not found</h2>
      <p>The meeting you're looking for doesn't exist or you don't have access.</p>
      <Button 
        label="Go Back to Meetings" 
        icon="pi pi-arrow-left" 
        @click="$router.push('/meetings')" 
        class="p-button-rounded p-button-outlined"
      />
    </div>
    
    <div v-else>
      <div class="header">
        <h1>{{ meeting.title }}</h1>
        <Button 
          label="Back to Meetings" 
          icon="pi pi-arrow-left" 
          class="p-button-rounded p-button-secondary" 
          @click="$router.push('/meetings')"
        />
      </div>
      
      <div class="meeting-header">
        <div class="meeting-status">
          <Tag 
            :value="meetingStatus.label" 
            :severity="meetingStatus.severity" 
            :icon="meetingStatus.icon"
          />
        </div>
      </div>
      
      <div class="meeting-content">
        <div class="left-panel">
          <Card class="meeting-detail-card">
            <template #title>
              <h2>{{ meeting.title }}</h2>
            </template>
            <template #subtitle>
              <div class="meeting-time">
                <i class="pi pi-calendar"></i>
                <span>{{ formatDate(meeting.t1) }} - {{ formatDate(meeting.t2) }}</span>
              </div>
            </template>
            <template #content>
              <div class="meeting-description">
                <h3>Description</h3>
                <p>{{ meeting.description }}</p>
              </div>
              
              <div class="meeting-actions">
                <Button 
                  v-if="isActive && !hasJoined" 
                  label="Join Meeting" 
                  icon="pi pi-sign-in" 
                  @click="joinMeeting" 
                  class="p-button-success p-button-raised"
                />
                <Button 
                  v-if="hasJoined" 
                  label="Go to Chat" 
                  icon="pi pi-comments" 
                  @click="$router.push('/chat')" 
                  class="p-button-info p-button-raised"
                />
                <Button 
                  v-if="hasJoined" 
                  label="Leave Meeting" 
                  icon="pi pi-sign-out" 
                  @click="leaveMeeting" 
                  class="p-button-danger p-button-outlined"
                />
              </div>
            </template>
          </Card>
        </div>
        
        <div class="right-panel">
          <Card class="details-card">
            <template #title>
              <h3>Meeting Details</h3>
            </template>
            <template #content>
              <div class="location-section">
                <h4>Location</h4>
                <div ref="mapContainer" class="map-container"></div>
              </div>
              
              <div class="participants-section">
                <h4>Participants ({{ participants.length }})</h4>
                <div v-if="loadingParticipants" class="loading-participants">
                  <ProgressSpinner style="width: 30px; height: 30px" />
                </div>
                <div v-else>
                  <ul class="participants-list">
                    <li v-for="(participant, index) in participants" :key="index" class="participant-item">
                      <Avatar 
                        :label="getInitials(participant)" 
                        shape="circle" 
                        :style="{ backgroundColor: getAvatarColor(participant) }" 
                      />
                      <span class="participant-name">{{ participant }}</span>
                      <Tag 
                        v-if="joinedParticipants.includes(participant)" 
                        value="Joined" 
                        severity="success" 
                        icon="pi pi-check-circle"
                      />
                    </li>
                  </ul>
                </div>
              </div>
            </template>
          </Card>

          <Card v-if="hasJoined" class="chat-section chat-card">
            <template #title>
              <h3>Meeting Chat</h3>
            </template>
            <template #content>
              <div class="chat-container">
                <div class="messages-container" ref="messagesContainer">
                  <div v-if="loadingMessages" class="loading-messages">
                    <ProgressSpinner style="width: 30px; height: 30px" />
                  </div>
                  <div v-else-if="messages.length === 0" class="no-messages">
                    <p>No messages yet</p>
                  </div>
                  <div v-else class="message-list">
                    <div 
                      v-for="(message, index) in messages" 
                      :key="index" 
                      class="message-item"
                      :class="{ 'own-message': message.email === currentUser.email }"
                    >
                      <div class="message-content">
                        <div class="message-header">
                          <span class="message-sender">{{ message.email }}</span>
                          <small class="message-time">{{ formatTime(message.timestamp) }}</small>
                        </div>
                        <div class="message-text">{{ message.message }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="message-input">
                  <InputText 
                    v-model="newMessage" 
                    placeholder="Type a message..." 
                    class="p-inputtext-lg"
                    @keyup.enter="sendMessage"
                  />
                  <Button 
                    icon="pi pi-send" 
                    @click="sendMessage" 
                    :disabled="!newMessage.trim()"
                    class="p-button-rounded"
                  />
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import { useStore } from 'vuex';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import L from 'leaflet';

export default {
  name: 'MeetingDetails',
  setup() {
    const store = useStore();
    const route = useRoute();
    const router = useRouter();
    const toast = useToast();
    
    const loading = ref(true);
    const loadingParticipants = ref(false);
    const loadingMessages = ref(false);
    const meeting = ref(null);
    const participants = ref([]);
    const joinedParticipants = ref([]);
    const messages = ref([]);
    const newMessage = ref('');
    const mapInstance = ref(null);
    const mapContainer = ref(null);
    const messagesContainer = ref(null);
    
    // Chat polling
    const pollingInterval = ref(null);
    
    const meetingId = computed(() => Number(route.params.id));
    const currentUser = computed(() => store.getters.currentUser);
    const isActive = computed(() => {
      if (!meeting.value) return false;
      const now = new Date();
      const startTime = new Date(meeting.value.t1);
      const endTime = new Date(meeting.value.t2);
      return startTime <= now && endTime >= now;
    });
    
    const hasJoined = computed(() => {
      const joinedMeeting = store.getters.joinedMeeting;
      return joinedMeeting && joinedMeeting.meeting_id === meetingId.value;
    });
    
    const meetingStatus = computed(() => {
      if (!meeting.value) return { label: 'Unknown', severity: 'secondary', icon: 'pi pi-question-circle' };
      
      const now = new Date();
      const startTime = new Date(meeting.value.t1);
      const endTime = new Date(meeting.value.t2);
      
      if (startTime > now) {
        return { label: 'Upcoming', severity: 'info', icon: 'pi pi-calendar-plus' };
      } else if (startTime <= now && endTime >= now) {
        return { label: 'Active', severity: 'success', icon: 'pi pi-check-circle' };
      } else {
        return { label: 'Ended', severity: 'danger', icon: 'pi pi-times-circle' };
      }
    });
    
    onMounted(async () => {
      try {
        await fetchMeeting();
        if (meeting.value) {
          // Initialize map after meeting data is loaded
          nextTick(() => {
            initMap();
          });
          
          // Load participants
          await fetchParticipants();
          
          // If joined, load messages and start polling
          if (hasJoined.value) {
            await fetchMessages();
            startPolling();
          }
        }
      } catch (error) {
        console.error('Error in onMounted:', error);
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load meeting details',
          life: 3000
        });
      } finally {
        loading.value = false;
      }
    });
    
    onBeforeUnmount(() => {
      // Clean up map and polling
      if (mapInstance.value) {
        mapInstance.value.remove();
      }
      stopPolling();
    });
    
    // Watch for changes in hasJoined to start/stop polling
    watch(hasJoined, (newValue) => {
      if (newValue) {
        fetchMessages();
        startPolling();
      } else {
        stopPolling();
      }
    });
    
    const fetchMeeting = async () => {
      try {
        meeting.value = await store.dispatch('getMeeting', meetingId.value);
      } catch (error) {
        meeting.value = null;
        console.error('Error fetching meeting:', error);
      }
    };
    
    const fetchParticipants = async () => {
      loadingParticipants.value = true;
      try {
        // Parse participants from meeting data
        if (meeting.value && meeting.value.participants) {
          participants.value = meeting.value.participants.split(',').map(p => p.trim());
        }
        
        // Get joined participants if meeting is active
        if (isActive.value) {
          joinedParticipants.value = await store.dispatch('getMeetingParticipants', meetingId.value);
        }
      } catch (error) {
        console.error('Error fetching participants:', error);
      } finally {
        loadingParticipants.value = false;
      }
    };
    
    const fetchMessages = async () => {
      if (!hasJoined.value) return;
      
      loadingMessages.value = true;
      try {
        messages.value = await store.dispatch('getMeetingMessages', meetingId.value);
        // Scroll to bottom of messages
        nextTick(() => {
          if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
          }
        });
      } catch (error) {
        console.error('Error fetching messages:', error);
      } finally {
        loadingMessages.value = false;
      }
    };
    
    const joinMeeting = async () => {
      try {
        const result = await store.dispatch('joinMeeting', meetingId.value);
        if (result.success) {
          toast.add({
            severity: 'success',
            summary: 'Success',
            detail: 'You have joined the meeting',
            life: 3000
          });
          await fetchParticipants();
          await fetchMessages();
          startPolling();
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
    
    const leaveMeeting = async () => {
      try {
        const result = await store.dispatch('leaveMeeting', meetingId.value);
        if (result.success) {
          toast.add({
            severity: 'success',
            summary: 'Success',
            detail: 'You have left the meeting',
            life: 3000
          });
          stopPolling();
          await fetchParticipants();
        }
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to leave meeting',
          life: 3000
        });
      }
    };
    
    const sendMessage = async () => {
      if (!newMessage.value.trim() || !hasJoined.value) return;
      
      try {
        await store.dispatch('postMessage', {
          text: newMessage.value,
          meetingId: meetingId.value
        });
        
        // Clear input and fetch updated messages
        newMessage.value = '';
        await fetchMessages();
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to send message',
          life: 3000
        });
      }
    };
    
    const initMap = () => {
      if (!mapContainer.value || !meeting.value) return;
      
      // Initialize map centered on meeting location
      mapInstance.value = L.map(mapContainer.value).setView(
        [meeting.value.lat, meeting.value.long], 
        15
      );
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(mapInstance.value);
      
      // Add marker for meeting location
      L.marker([meeting.value.lat, meeting.value.long])
        .addTo(mapInstance.value)
        .bindPopup(meeting.value.title)
        .openPopup();
    };
    
    const startPolling = () => {
      if (pollingInterval.value) return;
      
      // Poll for new messages every 10 seconds
      pollingInterval.value = setInterval(() => {
        fetchMessages();
        fetchParticipants();
      }, 10000);
    };
    
    const stopPolling = () => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value);
        pollingInterval.value = null;
      }
    };
    
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString();
    };
    
    const formatTime = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
    
    const getInitials = (email) => {
      return email.substring(0, 2).toUpperCase();
    };
    
    const getAvatarColor = (email) => {
      // Generate a consistent color based on email string
      let hash = 0;
      for (let i = 0; i < email.length; i++) {
        hash = email.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      const hue = hash % 360;
      return `hsl(${hue}, 70%, 60%)`;
    };
    
    return {
      loading,
      loadingParticipants,
      loadingMessages,
      meeting,
      participants,
      joinedParticipants,
      messages,
      newMessage,
      mapContainer,
      messagesContainer,
      currentUser,
      isActive,
      hasJoined,
      meetingStatus,
      joinMeeting,
      leaveMeeting,
      sendMessage,
      formatDate,
      formatTime,
      getInitials,
      getAvatarColor
    };
  }
};
</script>

<style>
/* Import Leaflet CSS */
@import 'leaflet/dist/leaflet.css';

.meeting-details-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
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

.loading-container,
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
}

.meeting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  background-color: var(--surface-card);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.meeting-content {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 1.5rem;
}

.meeting-detail-card,
.details-card,
.chat-card {
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
  overflow: hidden;
}

.meeting-detail-card:hover,
.details-card:hover,
.chat-card:hover {
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.meeting-time {
  display: flex;
  align-items: center;
  color: var(--text-color-secondary);
}

.meeting-time i {
  margin-right: 0.5rem;
}

.meeting-description {
  margin-bottom: 2rem;
}

.meeting-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.map-container {
  height: 250px;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.participants-section {
  margin-top: 1.5rem;
}

.participants-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.participant-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--surface-border);
}

.participant-item:last-child {
  border-bottom: none;
}

.participant-name {
  margin-left: 0.75rem;
  flex: 1;
}

.chat-section {
  margin-top: 1.5rem;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 400px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: var(--surface-ground);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.no-messages {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: var(--text-color-secondary);
}

.loading-messages,
.loading-participants {
  display: flex;
  justify-content: center;
  padding: 1rem;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message-item {
  max-width: 80%;
}

.own-message {
  align-self: flex-end;
}

.message-content {
  padding: 0.75rem;
  border-radius: 8px;
  background: var(--primary-color-lightest, #f0f7ff);
}

.own-message .message-content {
  background: var(--primary-color, #2196F3);
  color: white;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.own-message .message-header {
  color: rgba(255, 255, 255, 0.9);
}

.message-sender {
  font-weight: 600;
}

.message-time {
  opacity: 0.7;
}

.message-input {
  display: flex;
  gap: 0.5rem;
}

.message-input .p-inputtext {
  flex: 1;
}

@media (max-width: 991px) {
  .meeting-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .meeting-details-container {
    padding: 1rem;
  }
  
  .meeting-actions {
    flex-direction: column;
  }
}
</style>