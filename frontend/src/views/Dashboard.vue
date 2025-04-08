<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>Welcome, {{ currentUser?.name || 'User' }}!</h1>
      <div class="dashboard-stats">
        <div class="stat-card">
          <i class="pi pi-calendar stat-icon"></i>
          <div class="stat-info">
            <div class="stat-value">{{ activeMeetings.length }}</div>
            <div class="stat-label">Active Meetings</div>
          </div>
        </div>
        <div class="stat-card" v-if="joinedMeeting">
          <i class="pi pi-users stat-icon"></i>
          <div class="stat-info">
            <div class="stat-value">{{ participants.length }}</div>
            <div class="stat-label">Participants in Your Meeting</div>
          </div>
        </div>
        <div class="stat-card">
          <i class="pi pi-map-marker stat-icon"></i>
          <div class="stat-info">
            <div class="stat-value">{{ nearbyMeetings.length }}</div>
            <div class="stat-label">Nearby Meetings</div>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-content">


      <div class="full-width-card">
        <Card class="dashboard-card status-card">
          <template #title>
            <div class="card-title">
              <i class="pi pi-compass mr-2"></i>
              Your Current Status
            </div>
          </template>
          <template #content>
            <div v-if="joinedMeeting" class="current-meeting">
              <div class="status-content">
                <div class="status-icon success">
                  <i class="pi pi-users"></i>
                </div>
                <div class="status-details">
                  <h3>You're in a meeting</h3>
                  <div class="meeting-info">
                    <div class="meeting-title">{{ joinedMeeting.title }}</div>
                    <div class="meeting-time">
                      <i class="pi pi-clock mr-2"></i>
                      {{ formatTime(joinedMeeting.t1) }} - {{ formatTime(joinedMeeting.t2) }}
                    </div>
                    <div class="meeting-location" v-if="userLocation">
                      <i class="pi pi-map-marker mr-2"></i>
                      <span>Location active</span>
                    </div>
                  </div>
                </div>
                <div class="status-actions">
                  <Button
                    label="Open Chat"
                    icon="pi pi-comments"
                    class="p-button-success p-button-lg mr-2"
                    @click="openChat"
                  />
                  <Button
                    label="Leave"
                    icon="pi pi-sign-out"
                    class="p-button-danger p-button-lg"
                    @click="confirmLeave"
                  />
                </div>
              </div>
            </div>
            <div v-else class="no-meeting">
              <div class="status-content">
                <div class="status-icon neutral">
                  <i class="pi pi-info-circle"></i>
                </div>
                <div class="status-details">
                  <h3>You're not in any meeting</h3>
                  <p>Join an existing meeting or create a new one to start collaborating with others.</p>
                </div>
                <div class="status-actions">
                  <Button
                    label="Find Nearby Meetings"
                    icon="pi pi-search"
                    class="p-button-raised p-button-info p-button-lg mr-2"
                    @click="findMeetings"
                  />
                  <Button
                    label="Create Meeting"
                    icon="pi pi-plus"
                    class="p-button-raised p-button-success p-button-lg"
                    @click="createMeeting"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>

        <div class="dashboard-col">
        <Card class="dashboard-card">
          <template #title>
            <div class="card-title">
              <i class="pi pi-calendar mr-2"></i>
              Active Meetings
            </div>
          </template>
          <template #content>
            <div v-if="activeMeetings.length > 0" class="meetings-list">
              <div v-for="meeting in activeMeetings" :key="meeting.meeting_id" class="meeting-item">
                <div class="meeting-item-content">
                  <div class="meeting-item-title">
                    <span>{{ meeting.title }}</span>
                    <div class="meeting-item-actions">
                      <Button
                        label="View"
                        icon="pi pi-info-circle"
                        class="p-button-outlined p-button-info"
                        @click="viewMeeting(meeting.meeting_id)"
                        style="margin-right: 0.5rem;"
                      />
                      <Button
                        label="Join"
                        icon="pi pi-sign-in"
                        class="p-button-success"
                        @click="joinMeeting(meeting.meeting_id)"
                        :disabled="isCurrentlyJoined(meeting.meeting_id)"
                      />
                    </div>
                  </div>
                  <div class="meeting-item-time">
                    <i class="pi pi-clock mr-1"></i>
                    {{ formatTime(meeting.t1) }} - {{ formatTime(meeting.t2) }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-meetings">
              <i class="pi pi-info-circle no-meetings-icon"></i>
              <p>No active meetings at the moment</p>
            </div>
          </template>
        </Card>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

export default {
  name: 'Dashboard',
  data() {
    return {
      map: null,
      marker: null,
      participants: []
    }
  },
  computed: {
    ...mapGetters(['currentUser', 'activeMeetings', 'nearbyMeetings', 'joinedMeeting', 'userLocation'])
  },
  methods: {
    formatTime(timeString) {
      const date = new Date(timeString)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
    isCurrentlyJoined(meetingId) {
      return this.joinedMeeting && this.joinedMeeting.meeting_id === meetingId
    },
    findMeetings() {
      this.$router.push('/meetings/find')
    },
    createMeeting() {
      this.$router.push('/meetings/create')
    },
    viewMeeting(meetingId) {
      this.$router.push(`/meetings/${meetingId}`)
    },
    openChat() {
      this.$router.push('/chat')
    },
    async joinMeeting(meetingId) {
      try {
        await this.$store.dispatch('joinMeeting', meetingId)
        this.$toast.add({
          severity: 'success',
          summary: 'Joined Meeting',
          detail: 'You have successfully joined the meeting',
          life: 3000
        })

        // Fetch participants
        this.fetchParticipants()
        
        // Redirect to chat immediately
        this.$router.push('/chat')
      } catch (error) {
        this.$toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to join meeting',
          life: 3000
        })
      }
    },
    confirmLeave() {
      this.$confirm.require({
        message: 'Are you sure you want to leave this meeting?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.leaveMeeting()
        }
      })
    },
    async leaveMeeting() {
      try {
        if (this.joinedMeeting) {
          await this.$store.dispatch('leaveMeeting', this.joinedMeeting.meeting_id)
          this.$toast.add({
            severity: 'info',
            summary: 'Left Meeting',
            detail: 'You have left the meeting',
            life: 3000
          })
        }
      } catch (error) {
        this.$toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to leave meeting',
          life: 3000
        })
      }
    },
    async fetchData() {
      try {
        await this.$store.dispatch('getActiveMeetings')

        // Get user location if not already set
        if (!this.userLocation) {
          this.getUserLocation()
        }

        // If the user is in a meeting, fetch participants
        if (this.joinedMeeting) {
          this.fetchParticipants()
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      }
    },
    async fetchParticipants() {
      if (this.joinedMeeting) {
        try {
          this.participants = await this.$store.dispatch('getMeetingParticipants', this.joinedMeeting.meeting_id)
        } catch (error) {
          console.error('Error fetching participants:', error)
        }
      }
    },
    getUserLocation() {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            const location = {
              lat: position.coords.latitude,
              lng: position.coords.longitude
            }
            this.$store.dispatch('setUserLocation', location)

            // Once we have location, fetch nearby meetings
            this.$store.dispatch('getNearbyMeetings', {
              x: location.lat,
              y: location.lng
            })
          },
          error => {
            console.error('Error getting location:', error)
            this.$toast.add({
              severity: 'warn',
              summary: 'Location Access',
              detail: 'Unable to access your location. Some features will be limited.',
              life: 5000
            })
          }
        )
      }
    },
    initMap() {
      if (this.userLocation && !this.map) {
        // Add a slight delay to ensure the DOM is ready
        setTimeout(() => {
          const mapElement = document.getElementById('location-map')
          if (mapElement) {
            this.map = L.map('location-map').setView(
              [this.userLocation.lat, this.userLocation.lng],
              15
            )

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '© OpenStreetMap contributors'
            }).addTo(this.map)

            this.marker = L.marker([this.userLocation.lat, this.userLocation.lng])
              .addTo(this.map)
              .bindPopup('Your Location')
              .openPopup()
          }
        }, 300)
      }
    }
  },
  watch: {
    userLocation() {
      this.initMap()
    }
  },
  mounted() {
    this.fetchData()
    // Set up auto-refresh
    this.refreshInterval = setInterval(() => {
      this.fetchData()
    }, 60000) // Refresh every minute
  },
  beforeUnmount() {
    // Clean up
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
    if (this.map) {
      this.map.remove()
      this.map = null
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}

.stat-card {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background: var(--surface-card);
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}

.stat-icon {
  font-size: 2rem;
  margin-right: 1rem;
  color: var(--primary-color);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.full-width-card {
  width: 100%;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem;
  background-color: var(--surface-section);
  border-radius: 8px;
}

.status-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  font-size: 2.5rem;
  flex-shrink: 0;
}

.status-icon.success {
  background-color: var(--green-100);
  color: var(--green-600);
}

.status-icon.neutral {
  background-color: var(--blue-100);
  color: var(--blue-600);
}

.status-details {
  flex: 1;
}

.status-details h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: var(--primary-color);
}

.status-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.dashboard-col {
  flex: 1;
  min-width: 300px;
}

.dashboard-card {
  margin-bottom: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
}

.current-meeting, .no-meeting {
  padding: 1rem 0;
}

.meeting-info {
  padding: 1rem;
  background: var(--surface-hover);
  border-radius: 6px;
}

.meeting-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.meeting-time {
  margin-bottom: 1rem;
  color: var(--text-color-secondary);
}

.meeting-buttons {
  display: flex;
  margin-top: 1rem;
}

.action-buttons {
  margin-top: 1.5rem;
}

.meetings-list {
  max-height: 400px;
  overflow-y: auto;
}

.meeting-item {
  padding: 1.5rem;
  border-bottom: 1px solid var(--surface-border);
  transition: background-color 0.2s;
}

.meeting-item:hover {
  background-color: var(--surface-hover);
}

.meeting-item:last-child {
  border-bottom: none;
}

.meeting-item-content {
  display: flex;
  flex-direction: column;
}

.meeting-item-title {
  font-weight: 700;
  font-size: 1.2rem;
  margin-bottom: 0.75rem;
  color: var(--primary-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meeting-item-time {
  font-size: 1rem;
  color: var(--text-color-secondary);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
}

.meeting-item-actions {
  display: flex;
  gap: 0.5rem;
}

.no-meetings {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: var(--text-color-secondary);
}

.no-meetings-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.location-map {
  height: 250px;
  border-radius: 6px;
  margin-top: 0.5rem;
}

@media (max-width: 768px) {
  .dashboard-content {
    flex-direction: column;
  }

  .dashboard-col {
    width: 100%;
  }
}
</style>