<template>
  <div class="create-meeting-container">
    <div class="header">
      <h1>Create New Meeting</h1>
      <Button
        label="Back to Meetings"
        icon="pi pi-arrow-left"
        class="p-button-rounded p-button-secondary"
        @click="$router.push('/meetings')"
      />
    </div>

    <Card>
      <template #title>
        <div class="card-header">
          <i class="pi pi-plus-circle mr-2"></i>
          Meeting Details
        </div>
      </template>
      <template #content>
        <form @submit.prevent="createMeeting" class="p-fluid">
          <div class="form-grid">
            <div class="field col-12">
              <label for="meeting-title">Meeting Title*</label>
              <InputText
                id="meeting-title"
                v-model="meeting.title"
                :class="{'p-invalid': submitted && !meeting.title}"
                required
                placeholder="Enter a descriptive title for your meeting"
                aria-labelledby="title-label"
              />
              <small id="title-label" v-if="submitted && !meeting.title" class="p-error">Title is required</small>
            </div>

            <div class="field col-12">
              <label for="meeting-description">Description</label>
              <Textarea
                id="meeting-description"
                v-model="meeting.description"
                rows="3"
                autoResize
                placeholder="Provide additional details about this meeting"
                aria-labelledby="description-label"
              />
              <small id="description-label" class="p-text-secondary">Optional: Provide more details about the meeting purpose</small>
            </div>

            <div class="field col-12 md:col-6">
              <label for="meeting-start-time">Start Time*</label>
              <Calendar
                id="meeting-start-time"
                v-model="meeting.startTime"
                showTime
                hourFormat="24"
                :minDate="new Date()"
                :class="{'p-invalid': submitted && !meeting.startTime}"
                required
                placeholder="Select start date and time"
                aria-labelledby="start-time-label"
              />
              <small id="start-time-label" v-if="submitted && !meeting.startTime" class="p-error">Start time is required</small>
            </div>

            <div class="field col-12 md:col-6">
              <label for="meeting-end-time">End Time*</label>
              <Calendar
                id="meeting-end-time"
                v-model="meeting.endTime"
                showTime
                hourFormat="24"
                :minDate="meeting.startTime || new Date()"
                :class="{'p-invalid': submitted && !validEndTime}"
                required
                placeholder="Select end date and time"
                aria-labelledby="end-time-label"
              />
              <small id="end-time-label" v-if="submitted && !meeting.endTime" class="p-error">End time is required</small>
              <small v-else-if="submitted && !validEndTime" class="p-error">End time must be after start time</small>
            </div>

            <div class="field col-12">
              <label>Meeting Location* <span class="location-help">(Click or drag on the map to set)</span></label>
              <div id="location-map" class="location-map"></div>
              <div v-if="hasLocationSelected" class="location-info">
                <i class="pi pi-map-marker"></i>
                <span v-if="locationAddress">{{ locationAddress }}</span>
                <span v-else>Location selected</span>
              </div>
              <small v-if="submitted && !hasLocationSelected" class="p-error">Please select a location on the map</small>
            </div>

            <!-- Lat/Long fields hidden from UI but kept in data model -->

            <div class="field col-12">
              <label for="meeting-participants">Participants (comma-separated emails)*</label>
              <Textarea
                id="meeting-participants"
                v-model="meeting.participants"
                rows="3"
                placeholder="email1@example.com, email2@example.com, ..."
                :class="{'p-invalid': submitted && !meeting.participants}"
                required
                aria-labelledby="participants-label"
              />
              <small id="participants-label" v-if="submitted && !meeting.participants" class="p-error">At least one participant is required</small>
              <small class="p-text-secondary">Note: You will be automatically added as a participant.</small>
            </div>
          </div>

          <div class="action-buttons">
            <Button
              type="button"
              label="Cancel"
              icon="pi pi-times"
              class="p-button-secondary mr-2"
              @click="cancel"
            />
            <Button
              type="submit"
              label="Create Meeting"
              icon="pi pi-check"
              :loading="loading"
            />
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import axios from 'axios'

export default {
  name: 'CreateMeeting',
  data() {
    return {
      meeting: {
        title: '',
        description: '',
        startTime: null,
        endTime: null,
        latitude: null,
        longitude: null,
        participants: ''
      },
      map: null,
      marker: null,
      submitted: false,
      loading: false,
      locationAddress: '',
      geocodeLoading: false
    }
  },
  computed: {
    ...mapGetters(['currentUser', 'userLocation']),
    validEndTime() {
      if (!this.meeting.startTime || !this.meeting.endTime) return true
      return this.meeting.endTime > this.meeting.startTime
    },
    hasLocationSelected() {
      return this.meeting.latitude !== null && this.meeting.longitude !== null
    }
  },
  methods: {
    initMap() {
      if (this.map) return

      // Create map
      this.map = L.map('location-map').setView([0, 0], 15)

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(this.map)

      // Add click handler to update location
      this.map.on('click', (e) => {
        this.meeting.latitude = e.latlng.lat
        this.meeting.longitude = e.latlng.lng
        this.updateMarker()
        this.reverseGeocode(e.latlng.lat, e.latlng.lng)
      })

      // Try to get user's current location
      this.getUserLocation()
    },
    getUserLocation() {
      // If we already have the user location from the store, use it
      if (this.userLocation) {
        this.meeting.latitude = this.userLocation.lat
        this.meeting.longitude = this.userLocation.lng
        this.map.setView([this.userLocation.lat, this.userLocation.lng], 15)
        this.updateMarker()
        this.reverseGeocode(this.userLocation.lat, this.userLocation.lng)
        return
      }

      // Otherwise try to get from browser
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            this.meeting.latitude = position.coords.latitude
            this.meeting.longitude = position.coords.longitude

            // Center map on user's location
            this.map.setView([this.meeting.latitude, this.meeting.longitude], 15)
            this.updateMarker()
            this.reverseGeocode(position.coords.latitude, position.coords.longitude)
          },
          error => {
            console.error('Error getting location:', error)
            this.$toast.add({
              severity: 'info',
              summary: 'Location Access',
              detail: 'Click on the map to set meeting location',
              life: 5000
            })

            // Set default location - Athens, Greece
            this.map.setView([37.9838, 23.7275], 13)
          }
        )
      }
    },
    updateMarker() {
      // Remove existing marker if any
      if (this.marker) {
        this.map.removeLayer(this.marker)
      }

      // Add new marker
      this.marker = L.marker([this.meeting.latitude, this.meeting.longitude], {
        draggable: true
      })
        .addTo(this.map)
        .bindPopup('Meeting Location')
        .openPopup()

      // Update location when marker is dragged
      this.marker.on('dragend', (e) => {
        const marker = e.target
        const position = marker.getLatLng()
        this.meeting.latitude = position.lat
        this.meeting.longitude = position.lng
        this.reverseGeocode(position.lat, position.lng)
      })
    },
    async reverseGeocode(lat, lng) {
      try {
        this.geocodeLoading = true
        // Use Nominatim OpenStreetMap service for reverse geocoding
        const response = await axios.get(`https://nominatim.openstreetmap.org/reverse`, {
          params: {
            lat,
            lon: lng,
            format: 'json'
          },
          headers: {
            'Accept-Language': 'en'
          }
        })

        if (response.data && response.data.display_name) {
          this.locationAddress = response.data.display_name
        } else {
          this.locationAddress = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
        }
      } catch (error) {
        console.error('Geocoding error:', error)
        // Fallback to coordinates if geocoding fails
        this.locationAddress = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      } finally {
        this.geocodeLoading = false
      }
    },
    ensureUserInParticipants() {
      if (!this.currentUser) return

      // Make sure current user is in participants list
      const participants = this.meeting.participants.split(',')
        .map(p => p.trim())
        .filter(p => p) // Remove empty entries

      if (!participants.includes(this.currentUser.email)) {
        if (participants.length > 0) {
          this.meeting.participants += `, ${this.currentUser.email}`
        } else {
          this.meeting.participants = this.currentUser.email
        }
      }
    },
    validateEmails(emails) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      const invalidEmails = []

      const emailList = emails.split(',')
        .map(email => email.trim())
        .filter(email => email)

      for (const email of emailList) {
        if (!emailRegex.test(email)) {
          invalidEmails.push(email)
        }
      }

      return {
        valid: invalidEmails.length === 0,
        invalidEmails
      }
    },
    async createMeeting() {
      this.submitted = true

      // Basic validation
      if (!this.meeting.title) {
        this.$toast.add({
          severity: 'error',
          summary: 'Required Field',
          detail: 'Please enter a meeting title',
          life: 3000
        })
        return
      }

      if (!this.meeting.startTime || !this.meeting.endTime) {
        this.$toast.add({
          severity: 'error',
          summary: 'Required Fields',
          detail: 'Please select both start and end times',
          life: 3000
        })
        return
      }

      if (!this.validEndTime) {
        this.$toast.add({
          severity: 'error',
          summary: 'Invalid Time Range',
          detail: 'End time must be after start time',
          life: 3000
        })
        return
      }

      if (!this.hasLocationSelected) {
        this.$toast.add({
          severity: 'error',
          summary: 'Location Required',
          detail: 'Please select a meeting location on the map',
          life: 3000
        })
        return
      }

      if (!this.meeting.participants) {
        this.$toast.add({
          severity: 'error',
          summary: 'Participants Required',
          detail: 'Please add at least one participant',
          life: 3000
        })
        return
      }

      // Validate email format
      const emailValidation = this.validateEmails(this.meeting.participants)
      if (!emailValidation.valid) {
        this.$toast.add({
          severity: 'error',
          summary: 'Invalid Email Format',
          detail: `These emails are invalid: ${emailValidation.invalidEmails.join(', ')}`,
          life: 5000
        })
        return
      }

      // Ensure current user is included in participants
      this.ensureUserInParticipants()

      try {
        this.loading = true

        const meetingData = {
          title: this.meeting.title,
          description: this.meeting.description || '',
          t1: this.meeting.startTime.toISOString(),
          t2: this.meeting.endTime.toISOString(),
          lat: this.meeting.latitude,
          long: this.meeting.longitude,
          participants: this.meeting.participants
        }

        const result = await this.$store.dispatch('createMeeting', meetingData)

        if (result.meeting_id) {
          // Show success message
          this.$toast.add({
            severity: 'success',
            summary: 'Meeting Created',
            detail: `Meeting "${this.meeting.title}" has been created successfully`,
            life: 3000
          })

          console.log('Meeting created with ID:', result.meeting_id)

          // Wait a bit for backend to fully process the meeting
          await new Promise(resolve => setTimeout(resolve, 500))

          // Force refresh meetings list multiple times with increasing delays
          console.log('Refreshing meetings list after creation - attempt 1')
          try {
            const meetings = await this.$store.dispatch('getActiveMeetings', { forceRefresh: true })
            console.log('Meetings refreshed (attempt 1), found:', meetings)

            // If no meetings found, try again after a delay
            if (!meetings || meetings.length === 0) {
              await new Promise(resolve => setTimeout(resolve, 1000))
              console.log('Refreshing meetings list after creation - attempt 2')
              const meetings2 = await this.$store.dispatch('getActiveMeetings', { forceRefresh: true })
              console.log('Meetings refreshed (attempt 2), found:', meetings2)
            }
          } catch (error) {
            console.error('Error refreshing meetings:', error)
          }

          // Create a delay to ensure everything is updated
          setTimeout(() => {
            // Navigate back to meetings list
            this.$router.push('/meetings')
          }, 500)
        } else {
          throw new Error('Failed to create meeting - no meeting ID returned')
        }
      } catch (error) {
        console.error('Meeting creation error:', error)
        this.$toast.add({
          severity: 'error',
          summary: 'Creation Error',
          detail: error.response?.data?.detail || error.message || 'Failed to create meeting',
          life: 5000
        })
      } finally {
        this.loading = false
      }
    },
    cancel() {
      this.$router.push('/meetings')
    }
  },
  mounted() {
    // If user is not logged in, redirect to login
    if (!this.currentUser) {
      this.$router.push('/login')
      return
    }

    // Initialize map
    this.$nextTick(() => {
      this.initMap()
    })

    // Set default meeting times
    const now = new Date()
    this.meeting.startTime = new Date(now.getTime() + 60 * 60 * 1000) // 1 hour from now
    this.meeting.endTime = new Date(now.getTime() + 2 * 60 * 60 * 1000) // 2 hours from now
  },
  beforeUnmount() {
    // Clean up map
    if (this.map) {
      this.map.remove()
    }
  }
}
</script>

<style scoped>
.create-meeting-container {
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

.card-header {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
  color: var(--primary-color, #4CAF50);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
}

.col-12 {
  grid-column: span 12;
}

.md\:col-6 {
  grid-column: span 12;
}

.location-map {
  height: 350px;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  border: 1px solid #ddd;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.location-help {
  font-size: 0.9rem;
  color: #666;
  font-style: italic;
  margin-left: 0.5rem;
}

.location-info {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  margin: 0.5rem 0;
  font-size: 0.9rem;
  color: #555;
}

.location-info i {
  margin-right: 0.5rem;
  color: var(--primary-color, #4CAF50);
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 2rem;
  gap: 1rem;
}

label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  display: inline-block;
}

.p-inputtext:focus {
  box-shadow: 0 0 0 1px var(--primary-color, #4CAF50);
}

/* Add a little animation for success feedback */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.p-button[type="submit"]:not(:disabled):active {
  animation: pulse 0.3s ease;
}

@media (min-width: 768px) {
  .md\:col-6 {
    grid-column: span 6;
  }
}

@media (max-width: 480px) {
  .create-meeting-container {
    margin: 1rem;
  }

  .form-grid {
    gap: 0.75rem;
  }

  .location-map {
    height: 250px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .p-button {
    margin-right: 0;
    margin-bottom: 0.5rem;
  }
}
</style>