<template>
  <div class="find-meetings-container">
    <div class="header">
      <h1>Find Nearby Meetings</h1>
      <Button
        label="Create Meeting"
        icon="pi pi-plus"
        class="p-button-rounded p-button-success"
        @click="$router.push('/meetings/create')"
      />
    </div>

    <Card>
      <template #title>
        <div class="card-header">
          <i class="pi pi-map-marker mr-2"></i>
          Select Location
        </div>
      </template>
      <template #content>
        <div class="p-fluid">
          <div id="map" class="map-container"></div>

          <div class="map-details mt-3">
            <div class="location-info">
              <i class="pi pi-map-marker"></i>
              <div v-if="locationAddress">
                {{ locationAddress }}
              </div>
              <div v-else>
                Selected Location
              </div>
              <div class="ml-auto">
                <Button
                  icon="pi pi-refresh"
                  class="p-button-rounded p-button-text p-button-sm"
                  @click="getUserLocation"
                  title="Use my current location"
                />
              </div>
            </div>
            <div class="search-actions">
              <Button
                label="Find Nearby Meetings"
                icon="pi pi-search"
                class="p-button-raised"
                :loading="loading"
                @click="findNearbyMeetings"
              />
              <Button
                label="Create Meeting Here"
                icon="pi pi-plus"
                class="p-button-outlined"
                @click="createMeetingAtLocation"
              />
            </div>
          </div>

          <Divider />

          <div class="meetings-section">
            <h3>Nearby Meetings</h3>

            <div v-if="nearbyMeetings.length === 0" class="no-meetings">
              <i class="pi pi-info-circle mr-2"></i>
              <span>No nearby meetings found. Try a different location or create your own meeting.</span>
            </div>

            <div v-else class="meeting-cards">
              <Card v-for="meeting in nearbyMeetings" :key="meeting.meeting_id" class="meeting-card">
                <template #title>
                  <div class="meeting-title">{{ meeting.title }}</div>
                </template>
                <template #content>
                  <div class="meeting-details">
                    <div class="meeting-time">
                      <i class="pi pi-calendar mr-2"></i>
                      <span>{{ formatDate(meeting.t1) }}</span>
                    </div>
                    <div class="meeting-time">
                      <i class="pi pi-clock mr-2"></i>
                      <span>{{ formatTime(meeting.t1) }} - {{ formatTime(meeting.t2) }}</span>
                    </div>
                    <div class="meeting-description">
                      {{ meeting.description || 'No description provided' }}
                    </div>
                    <div class="meeting-participants">
                      <strong>Participants: </strong> {{ meeting.participants.split(',').length }}
                    </div>
                    <div class="meeting-location">
                      <strong>Distance: </strong>
                      {{ calculateDistance(location.lat, location.lng, meeting.lat, meeting.long).toFixed(0) }} meters away
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div class="meeting-actions">
                    <Button
                      label="View Details"
                      icon="pi pi-info-circle"
                      class="p-button-secondary mr-2"
                      @click="viewMeeting(meeting.meeting_id)"
                    />
                    <Button
                      label="Join"
                      icon="pi pi-sign-in"
                      :disabled="isCurrentlyJoined(meeting.meeting_id)"
                      @click="joinMeeting(meeting.meeting_id)"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </div>
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
  name: 'FindMeetings',
  data() {
    return {
      map: null,
      userMarker: null,
      meetingMarkers: [],
      location: {
        lat: 0,
        lng: 0
      },
      locationAddress: '',
      loading: false,
      geocodeLoading: false
    }
  },
  computed: {
    ...mapGetters(['nearbyMeetings', 'joinedMeeting'])
  },
  methods: {
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },
    formatTime(timeString) {
      const date = new Date(timeString)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
    isCurrentlyJoined(meetingId) {
      return this.joinedMeeting && this.joinedMeeting.meeting_id === meetingId
    },
    calculateDistance(lat1, lon1, lat2, lon2) {
      // Haversine formula
      const R = 6371e3 // Earth radius in meters
      const φ1 = this.toRadians(lat1)
      const φ2 = this.toRadians(lat2)
      const Δφ = this.toRadians(lat2 - lat1)
      const Δλ = this.toRadians(lon2 - lon1)

      const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2)
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
      const d = R * c

      return d
    },
    toRadians(degrees) {
      return degrees * Math.PI / 180
    },
    initMap() {
      if (this.map) return;

      try {
        // Get the map container element
        const mapContainer = document.getElementById('map');
        if (!mapContainer) {
          console.error("Map container not found");
          return;
        }

        // Create map
        this.map = L.map('map', {
          // Add animation false to prevent potential issues
          fadeAnimation: false,
          zoomAnimation: false
        }).setView([0, 0], 15);

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add click handler to update location
        this.map.on('click', (e) => {
          this.location.lat = e.latlng.lat;
          this.location.lng = e.latlng.lng;
          this.updateMarker();
          this.reverseGeocode(e.latlng.lat, e.latlng.lng);
        });

        // Try to get user's current location
        this.getUserLocation();
      } catch (e) {
        console.error("Error initializing map:", e);
        this.$toast.add({
          severity: 'error',
          summary: 'Map Error',
          detail: 'Could not initialize the map. Please try refreshing the page.',
          life: 5000
        });
      }
    },
    getUserLocation() {
      if (!navigator.geolocation) {
        this.$toast.add({
          severity: 'warn',
          summary: 'Geolocation Not Supported',
          detail: 'Your browser does not support geolocation. Please click on the map to set your location.',
          life: 5000
        });

        // Set default location to Athens, Greece
        if (this.map) {
          try {
            this.map.setView([37.9838, 23.7275], 13);
            this.location.lat = 37.9838;
            this.location.lng = 23.7275;
            this.locationAddress = 'Athens, Greece';
            this.updateMarker();
          } catch (e) {
            console.error("Error setting default location:", e);
          }
        }
        return;
      }

      navigator.geolocation.getCurrentPosition(
        position => {
          try {
            this.location.lat = position.coords.latitude;
            this.location.lng = position.coords.longitude;

            // Center map on user's location
            if (this.map) {
              this.map.setView([this.location.lat, this.location.lng], 15);
              this.updateMarker();
              this.reverseGeocode(this.location.lat, this.location.lng);
            }

            // Auto-find nearby meetings
            this.findNearbyMeetings();
          } catch (e) {
            console.error('Error processing location:', e);
            this.$toast.add({
              severity: 'error',
              summary: 'Map Error',
              detail: 'Error processing your location. Please try again.',
              life: 3000
            });
          }
        },
        error => {
          console.error('Error getting location:', error);
          this.$toast.add({
            severity: 'warn',
            summary: 'Location Access',
            detail: 'Unable to access your location. Please click on the map to set your position.',
            life: 5000
          });

          // Set default location to Athens, Greece
          if (this.map) {
            try {
              this.map.setView([37.9838, 23.7275], 13);
              this.location.lat = 37.9838;
              this.location.lng = 23.7275;
              this.locationAddress = 'Athens, Greece';
              this.updateMarker();
            } catch (e) {
              console.error("Error setting default location:", e);
            }
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    },
    updateMarker() {
      // Ensure map is initialized
      if (!this.map) return;

      // Remove existing marker if any
      if (this.userMarker) {
        try {
          this.map.removeLayer(this.userMarker);
        } catch (e) {
          console.warn("Error removing marker:", e);
          // Continue anyway
        }
      }

      // Add new marker with try-catch for safety
      try {
        this.userMarker = L.marker([this.location.lat, this.location.lng], {
          draggable: true
        })
          .addTo(this.map)
          .bindPopup('Your Location')
          .openPopup();

        // Update location when marker is dragged
        this.userMarker.on('dragend', (e) => {
          const marker = e.target;
          const position = marker.getLatLng();
          this.location.lat = position.lat;
          this.location.lng = position.lng;
          this.reverseGeocode(position.lat, position.lng);
        });
      } catch (e) {
        console.error("Error updating marker:", e);
        this.$toast.add({
          severity: 'error',
          summary: 'Map Error',
          detail: 'Error updating map marker. Please try refreshing the page.',
          life: 5000
        });
      }
    },
    updateMeetingMarkers() {
      // Ensure map is initialized
      if (!this.map) return;

      try {
        // Clear existing meeting markers safely
        this.meetingMarkers.forEach(marker => {
          try {
            if (marker && this.map) {
              this.map.removeLayer(marker);
            }
          } catch (e) {
            console.warn("Error removing meeting marker:", e);
          }
        });
        this.meetingMarkers = [];

        // Add markers for each nearby meeting
        this.nearbyMeetings.forEach(meeting => {
          try {
            const marker = L.marker([meeting.lat, meeting.long])
              .addTo(this.map)
              .bindPopup(`<b>${meeting.title}</b><br>${this.formatTime(meeting.t1)} - ${this.formatTime(meeting.t2)}`);

            marker.on('click', () => {
              this.$router.push(`/meetings/${meeting.meeting_id}`);
            });

            this.meetingMarkers.push(marker);
          } catch (e) {
            console.warn(`Error adding marker for meeting ${meeting.meeting_id}:`, e);
          }
        });
      } catch (e) {
        console.error("Error updating meeting markers:", e);
      }
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

    createMeetingAtLocation() {
      // Store the location in Vuex
      this.$store.dispatch('setUserLocation', {
        lat: this.location.lat,
        lng: this.location.lng
      })

      // Navigate to create meeting page
      this.$router.push('/create-meeting')
    },

    async findNearbyMeetings() {
      try {
        this.loading = true
        await this.$store.dispatch('getNearbyMeetings', {
          x: this.location.lat,
          y: this.location.lng
        })
        this.loading = false

        // Update markers on map
        this.updateMeetingMarkers()

        // Show a success message
        if (this.nearbyMeetings.length > 0) {
          this.$toast.add({
            severity: 'success',
            summary: 'Meetings Found',
            detail: `Found ${this.nearbyMeetings.length} nearby meetings`,
            life: 3000
          })
        } else {
          this.$toast.add({
            severity: 'info',
            summary: 'No Meetings Found',
            detail: 'No meetings found in this area. Why not create one?',
            life: 3000
          })
        }
      } catch (error) {
        this.loading = false
        this.$toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to find nearby meetings',
          life: 3000
        })
      }
    },
    viewMeeting(meetingId) {
      this.$router.push(`/meetings/${meetingId}`)
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

        // Navigate to dashboard
        this.$router.push('/')
      } catch (error) {
        this.$toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to join meeting',
          life: 3000
        })
      }
    }
  },
  mounted() {
    // Initialize map
    this.$nextTick(() => {
      this.initMap()
    })
  },
  beforeUnmount() {
    // Clean up map and markers
    try {
      // First remove all markers
      if (this.userMarker) {
        try {
          this.map?.removeLayer(this.userMarker);
        } catch (e) {
          console.warn("Error removing user marker during cleanup:", e);
        }
      }

      // Clean up meeting markers
      if (this.meetingMarkers && this.meetingMarkers.length > 0) {
        for (const marker of this.meetingMarkers) {
          try {
            if (marker && this.map) {
              this.map.removeLayer(marker);
            }
          } catch (e) {
            console.warn("Error removing meeting marker during cleanup:", e);
          }
        }
        this.meetingMarkers = [];
      }

      // Finally remove map instance
      if (this.map) {
        this.map.remove();
        this.map = null;
      }
    } catch (e) {
      console.error("Error during map cleanup:", e);
    }
  }
}
</script>

<style scoped>
.find-meetings-container {
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
}

.map-container {
  height: 400px;
  border-radius: 6px;
  z-index: 0;
}

.map-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.location-info {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.location-info i {
  font-size: 1.2rem;
  color: var(--primary-color, #4CAF50);
  margin-right: 0.75rem;
}

.search-actions {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.meeting-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.meeting-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.meeting-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.meeting-title {
  font-size: 1.25rem;
  font-weight: 600;
}

.meeting-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
}

.meeting-time, .meeting-location {
  display: flex;
  align-items: center;
  color: var(--text-color-secondary);
  font-size: 0.875rem;
}

.meeting-description {
  margin: 0.5rem 0;
  flex: 1;
}

.meeting-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.no-meetings {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: var(--surface-hover);
  border-radius: 6px;
  color: var(--text-color-secondary);
}

@media (max-width: 768px) {
  .search-actions {
    flex-direction: column;
  }

  .meeting-cards {
    grid-template-columns: 1fr;
  }

  .map-container {
    height: 300px;
  }
}

@media (max-width: 480px) {
  .find-meetings-container {
    margin: 0.5rem;
  }

  .location-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .location-info .ml-auto {
    width: 100%;
    display: flex;
    justify-content: flex-end;
  }

  .map-container {
    height: 250px;
  }
}
</style>