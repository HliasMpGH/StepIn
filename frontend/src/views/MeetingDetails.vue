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
        <!-- Two equal-sized cards at the top -->
        <div class="cards-container">
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
                  class="p-button-success p-button-raised p-button-lg"
                />
                <Button
                  v-if="hasJoined"
                  label="Go to Chat"
                  icon="pi pi-comments"
                  @click="$router.push('/chat')"
                  class="p-button-info p-button-raised p-button-lg"
                />
                <Button
                  v-if="hasJoined"
                  label="Leave Meeting"
                  icon="pi pi-sign-out"
                  @click="leaveMeeting"
                  class="p-button-danger p-button-outlined p-button-lg"
                />
              </div>
            </template>
          </Card>

          <Card class="details-card">
            <template #title>
              <h3>Meeting Details</h3>
            </template>
            <template #content>
              <div class="detail-item">
                <h4>Date & Time</h4>
                <div class="detail-content">
                  <i class="pi pi-calendar mr-2"></i>
                  <span>{{ formatDate(meeting.t1) }}</span>
                </div>
                <div class="detail-content">
                  <i class="pi pi-clock mr-2"></i>
                  <span>{{ formatTime(meeting.t1) }} - {{ formatTime(meeting.t2) }}</span>
                </div>
              </div>

              <div class="detail-item">
                <h4>Created By</h4>
                <div class="detail-content">
                  <i class="pi pi-user mr-2"></i>
                  <span>{{ meeting.email }}</span>
                </div>
              </div>

              <div class="detail-item">
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
        </div>
        
        <!-- Full-width location card -->
        <Card class="location-card">
          <template #title>
            <div class="location-title">
              <i class="pi pi-map mr-2"></i>
              <h3>Meeting Location</h3>
            </div>
          </template>
          <template #content>
            <div class="location-details">
              <!-- Location information - only show address if available -->
              <div class="location-info" v-if="locationAddress">
                <div class="address-section">
                  <i class="pi pi-building mr-2"></i>
                  <span>{{ locationAddress }}</span>
                </div>
              </div>
              
              <!-- The map container -->
              <div ref="mapContainer" class="map-container-full"></div>
              
              <!-- Map actions -->
              <div class="map-actions">
                <Button 
                  label="Get Directions in Google Maps" 
                  icon="pi pi-map" 
                  class="p-button p-button-success"
                  @click="openInMaps"
                />
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useStore } from 'vuex';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';

export default {
  name: 'MeetingDetails',
  setup() {
    const store = useStore();
    const route = useRoute();
    const router = useRouter();
    const toast = useToast();

    const meetingId = ref(Number(route.params.id));
    const loading = ref(true);
    const meeting = ref(null);
    const loadingParticipants = ref(false);
    const participants = ref([]);
    const joinedParticipants = ref([]);
    const loadingMessages = ref(false);
    const messages = ref([]);
    const newMessage = ref('');
    const mapContainer = ref(null);
    const mapInstance = ref(null);
    const messagesContainer = ref(null);
    const pollingInterval = ref(null);
    const locationAddress = ref('');
    const loadingAddress = ref(false);

    const currentUser = computed(() => store.getters.currentUser);
    const joinedMeeting = computed(() => store.getters.joinedMeeting);

    const hasJoined = computed(() => {
      return joinedMeeting.value &&
             joinedMeeting.value.meeting_id === meetingId.value;
    });

    const isActive = computed(() => {
      if (!meeting.value) return false;

      const now = new Date();
      const start = new Date(meeting.value.t1);
      const end = new Date(meeting.value.t2);

      return start <= now && end >= now;
    });

    const meetingStatus = computed(() => {
      if (!meeting.value) return { label: 'Unknown', severity: 'info', icon: 'pi pi-question-circle' };

      const now = new Date();
      const start = new Date(meeting.value.t1);
      const end = new Date(meeting.value.t2);

      if (now < start) {
        return { label: 'Upcoming', severity: 'info', icon: 'pi pi-calendar' };
      } else if (now >= start && now <= end) {
        return { label: 'Active', severity: 'success', icon: 'pi pi-check-circle' };
      } else {
        return { label: 'Ended', severity: 'danger', icon: 'pi pi-times-circle' };
      }
    });

    onMounted(async () => {
      try {
        await fetchMeeting();

        // If meeting details loaded successfully
        if (meeting.value) {
          // Initialize map - this will trigger address lookup
          initMap();

          // Fetch participants and messages
          await Promise.all([
            fetchParticipants(),
            fetchMessages()
          ]);

          // If user has joined this meeting, start polling for updates
          if (hasJoined.value) {
            startPolling();
          }
        }
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to load meeting details',
          life: 3000
        });
      } finally {
        loading.value = false;
      }
    });

    onBeforeUnmount(() => {
      stopPolling();

      // Clean up map if initialized
      if (mapInstance.value) {
        mapInstance.value.remove();
        mapInstance.value = null;
      }
    });

    watch(messagesContainer, () => {
      scrollToBottom();
    });

    watch(messages, () => {
      nextTick(() => {
        scrollToBottom();
      });
    });

    const fetchMeeting = async () => {
      try {
        meeting.value = await store.dispatch('getMeeting', meetingId.value);
      } catch (error) {
        console.error('Error fetching meeting:', error);
        meeting.value = null;
      }
    };

    const fetchParticipants = async () => {
      if (!meeting.value) return;

      loadingParticipants.value = true;
      try {
        // Get list of all participants from meeting data
        participants.value = meeting.value.participants.split(',').map(email => email.trim());

        // Get list of joined participants
        joinedParticipants.value = await store.dispatch('getMeetingParticipants', meetingId.value);
      } catch (error) {
        console.error('Error fetching participants:', error);
      } finally {
        loadingParticipants.value = false;
      }
    };

    const fetchMessages = async () => {
      if (!meeting.value || !hasJoined.value) return;

      loadingMessages.value = true;
      try {
        messages.value = await store.dispatch('getMeetingMessages', meetingId.value);
      } catch (error) {
        console.error('Error fetching messages:', error);
      } finally {
        loadingMessages.value = false;
      }
    };

    const joinMeeting = async () => {
      try {
        await store.dispatch('joinMeeting', meetingId.value);

        toast.add({
          severity: 'success',
          summary: 'Joined',
          detail: 'You have successfully joined the meeting',
          life: 3000
        });

        // Refresh participants and start polling for updates
        await fetchParticipants();
        await fetchMessages();
        startPolling();

        // Redirect to chat immediately
        router.push('/chat');
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
        await store.dispatch('leaveMeeting', meetingId.value);

        toast.add({
          severity: 'info',
          summary: 'Left',
          detail: 'You have left the meeting',
          life: 3000
        });

        // Stop polling and refresh participants
        stopPolling();
        await fetchParticipants();
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

      // Set a listener for when the DOM is fully loaded
      nextTick(() => {
        // Add slight delay to ensure the map container is properly rendered
        setTimeout(() => {
          try {
            console.log("Initializing map...");
            console.log("Map container:", mapContainer.value);
            console.log("Meeting coordinates:", meeting.value.lat, meeting.value.long);
            
            // Check if map was already initialized
            if (mapInstance.value) {
              console.log("Removing existing map instance");
              mapInstance.value.remove();
              mapInstance.value = null;
            }
            
            // Simple map initialization with minimum options to improve reliability
            mapInstance.value = L.map(mapContainer.value, {
              zoomControl: true,
              scrollWheelZoom: true,
              // Disable animations to prevent errors
              fadeAnimation: false,
              zoomAnimation: false
            }).setView([meeting.value.lat, meeting.value.long], 15);

            // Add basic tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '&copy; OpenStreetMap contributors'
            }).addTo(mapInstance.value);

            // Add a prominent marker for the meeting location
            const meetingIcon = L.icon({
              iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
              shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41]
            });
            
            const meetingMarker = L.marker([meeting.value.lat, meeting.value.long], {
              icon: meetingIcon,
              title: meeting.value.title
            }).addTo(mapInstance.value);
            
            // Simple popup with just the meeting title
            meetingMarker.bindPopup(`<b>${meeting.value.title}</b>`).openPopup();
            
            // Lookup address for this location
            lookupAddress();
            
            console.log("Map initialization complete");
            
            // Force resize to ensure proper display
            mapInstance.value.invalidateSize();
          } catch (error) {
            console.error('Error initializing map:', error);
            toast.add({
              severity: 'error',
              summary: 'Map Error',
              detail: 'Failed to initialize the map. Please try refreshing the page.',
              life: 3000
            });
          }
        }, 500); // Increased delay for better reliability
      });
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

    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    };

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    };

    const formatTime = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getInitials = (email) => {
      if (!email) return '??';

      // Get first letter of email local part
      const localPart = email.split('@')[0];
      return localPart.substring(0, 2).toUpperCase();
    };

    const getAvatarColor = (email) => {
      if (!email) return 'var(--primary-color)';

      // Generate color based on email string
      let hash = 0;
      for (let i = 0; i < email.length; i++) {
        hash = email.charCodeAt(i) + ((hash << 5) - hash);
      }

      const hue = hash % 360;
      return `hsl(${hue}, 70%, 60%)`;
    };

    // Method to lookup address from coordinates
    const lookupAddress = async () => {
      if (!meeting.value) return;
      
      loadingAddress.value = true;
      try {
        const response = await axios.get('https://nominatim.openstreetmap.org/reverse', {
          params: {
            format: 'json',
            lat: meeting.value.lat,
            lon: meeting.value.long,
            zoom: 18,
            addressdetails: 1
          },
          headers: {
            'Accept-Language': 'en',
            'User-Agent': 'StepIn Meeting App'
          }
        });
        
        if (response.data && response.data.display_name) {
          locationAddress.value = response.data.display_name;
        } else {
          toast.add({
            severity: 'info',
            summary: 'Address Not Found',
            detail: 'Could not find a readable address for this location',
            life: 3000
          });
        }
      } catch (error) {
        console.error('Error looking up address:', error);
        toast.add({
          severity: 'error',
          summary: 'Address Lookup Failed',
          detail: 'Unable to retrieve address information',
          life: 3000
        });
      } finally {
        loadingAddress.value = false;
      }
    };
    
    // Method to open location in Google Maps
    const openInMaps = () => {
      if (!meeting.value) return;
      
      const url = `https://www.google.com/maps/dir/?api=1&destination=${meeting.value.lat},${meeting.value.long}`;
      window.open(url, '_blank');
    };
    
    // Method to open location in OpenStreetMap
    const openOSM = () => {
      if (!meeting.value) return;
      
      const url = `https://www.openstreetmap.org/?mlat=${meeting.value.lat}&mlon=${meeting.value.long}&zoom=16`;
      window.open(url, '_blank');
    };

    return {
      meeting,
      loading,
      meetingId,
      participants,
      joinedParticipants,
      loadingParticipants,
      messages,
      loadingMessages,
      newMessage,
      currentUser,
      hasJoined,
      isActive,
      meetingStatus,
      mapContainer,
      messagesContainer,
      locationAddress,
      loadingAddress,
      joinMeeting,
      leaveMeeting,
      sendMessage,
      lookupAddress,
      openInMaps,
      openOSM,
      formatDate,
      formatTime,
      getInitials,
      getAvatarColor
    };
  }
}
</script>

<style scoped>
.meeting-details-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.loading-container,
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: 1rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.meeting-header {
  margin-bottom: 1.5rem;
}

.meeting-status {
  margin-bottom: 0.5rem;
}

.meeting-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-top: 2rem;
}

.cards-container {
  display: grid;
  grid-template-columns: minmax(300px, 1fr) minmax(300px, 1fr);
  gap: 2rem;
}

.meeting-detail-card, .details-card, .location-card, .chat-card {
  margin-bottom: 0;
  height: auto;
  min-height: 300px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  overflow: hidden;
  transition: none;
}

.location-card {
  width: 100%;
}

.map-container-full {
  height: 500px;
  border-radius: 8px;
  margin: 0.5rem 0 1rem 0;
  width: 100%;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--surface-border);
  z-index: 1; /* Ensure map controls work properly */
}

/* Fix leaflet popup styling */
:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.2);
}

:deep(.leaflet-popup-content) {
  margin: 12px 16px;
  line-height: 1.5;
}

:deep(.leaflet-control-zoom) {
  margin: 12px;
  border-radius: 4px;
  overflow: hidden;
}

:deep(.leaflet-control-scale) {
  margin: 8px 12px;
}

.meeting-description {
  margin-bottom: 1.5rem;
}

.meeting-description h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: var(--primary-color);
}

.meeting-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.detail-item {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--surface-200);
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.detail-item h4 {
  color: var(--primary-color);
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
  margin-top: 0;
}

.detail-content {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.map-container {
  height: 250px;
  border-radius: 8px;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
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
  color: #333; /* Dark text color for better readability */
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
  .cards-container {
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
  
  .map-container-full {
    height: 300px;
  }
  
  .map-actions {
    flex-direction: column;
  }
}

/* Location specific styles */
.location-title {
  display: flex;
  align-items: center;
}

.location-title h3 {
  margin: 0;
}

.location-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.location-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.address-section {
  display: flex;
  align-items: flex-start;
  background-color: var(--surface-ground);
  padding: 0.75rem;
  border-radius: 8px;
  margin-top: 0.5rem;
  line-height: 1.4;
}

.address-section i {
  margin-top: 3px;
}

.location-coordinates {
  font-family: monospace;
  background-color: var(--surface-ground);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.map-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.mt-2 {
  margin-top: 0.5rem;
}
</style>