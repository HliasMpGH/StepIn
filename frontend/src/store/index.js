import { createStore } from 'vuex'
import axios from 'axios'

// Base URL for API
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://127.0.0.1:8000/api',
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

export default createStore({
  state: {
    user: null,
    isAuthenticated: false,
    nearbyMeetings: [],
    activeMeetings: [],
    upcomingMeetings: [],
    currentMeeting: null,
    joinedMeeting: null,
    meetingParticipants: [],
    chatMessages: [],
    userMessages: [],
    userLocation: null,
    userCreatedMeetings: [],
    loading: false,
    error: null
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    currentUser: state => state.user,
    nearbyMeetings: state => state.nearbyMeetings,
    activeMeetings: state => state.activeMeetings,
    currentMeeting: state => state.currentMeeting,
    joinedMeeting: state => state.joinedMeeting,
    meetingParticipants: state => state.meetingParticipants,
    chatMessages: state => state.chatMessages,
    userMessages: state => state.userMessages,
    userLocation: state => state.userLocation,
    userCreatedMeetings: state => state.userCreatedMeetings,
    isLoading: state => state.loading,
    hasError: state => state.error !== null,
    errorMessage: state => state.error,
    upcomingMeetings: state => state.upcomingMeetings,
  },
  mutations: {
    SET_USER(state, user) {
      state.user = user
      state.isAuthenticated = user !== null
    },
    SET_UPCOMING_MEETINGS(state, meetings) {
      state.upcomingMeetings = meetings
    },
    SET_NEARBY_MEETINGS(state, meetings) {
      state.nearbyMeetings = meetings
    },
    SET_ACTIVE_MEETINGS(state, meetings) {
      state.activeMeetings = meetings
    },
    SET_CURRENT_MEETING(state, meeting) {
      state.currentMeeting = meeting
    },
    SET_JOINED_MEETING(state, meeting) {
      state.joinedMeeting = meeting
    },
    SET_MEETING_PARTICIPANTS(state, participants) {
      state.meetingParticipants = participants
    },
    SET_CHAT_MESSAGES(state, messages) {
      state.chatMessages = messages
    },
    SET_USER_MESSAGES(state, messages) {
      state.userMessages = messages
    },
    SET_USER_LOCATION(state, location) {
      state.userLocation = location
    },
    SET_USER_CREATED_MEETINGS(state, meetings) {
      state.userCreatedMeetings = meetings
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_ERROR(state) {
      state.error = null
    }
  },
  actions: {
    // User authentication
    login({ commit }, user) {
      // In a real app, this would validate with backend
      commit('SET_USER', user)
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout({ commit }) {
      commit('SET_USER', null)
      commit('SET_JOINED_MEETING', null)
      localStorage.removeItem('user')
    },
    checkAuth({ commit }) {
      const user = localStorage.getItem('user')
      if (user) {
        commit('SET_USER', JSON.parse(user))
      }
    },
    // User management
    async createUser({ commit }, userData) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.post('/users', userData)
        if (response.data.success) {
          // After creating user, login with it
          commit('SET_USER', {
            email: userData.email,
            name: userData.name,
            age: userData.age,
            gender: userData.gender
          })
          localStorage.setItem('user', JSON.stringify({
            email: userData.email,
            name: userData.name,
            age: userData.age,
            gender: userData.gender
          }))
        }
        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error creating user')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getUser({ commit }, email) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.get(`/users/${email}`)
        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error getting user details')
        commit('SET_LOADING', false)
        throw error
      }
    },
    // Meeting management
    async createMeeting({ commit, dispatch, state }, meetingData) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.post('/meetings', meetingData)

        // Force immediate refresh of active meetings after creation
        await dispatch('getActiveMeetings', { forceRefresh: true })

        // Also refresh user's created meetings
        if (state.user) {
          await dispatch('getUserCreatedMeetings')
        }

        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        console.error('Error creating meeting:', error.response || error)
        commit('SET_ERROR', error.response?.data?.error || 'Error creating meeting')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getMeeting({ commit }, meetingId) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.get(`/meetings/${meetingId}`)
        commit('SET_CURRENT_MEETING', response.data)
        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error getting meeting details')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getActiveMeetings({ commit }, { forceRefresh = false } = {}) {
      try {
        commit('SET_LOADING', true)

        console.log(`Getting active meetings... (forceRefresh=${forceRefresh})`)

        // Add a cache buster parameter for forceRefresh
        const cacheParam = forceRefresh ? `?cache=${Date.now()}` : ''

        // Normal API flow
        const response = await apiClient.get(`/meetings/active${cacheParam}`)
        console.log('Active meetings response:', response.data)

        // Check if meetings array exists
        if (!response.data.meetings) {
          console.log('No meetings found in response')
          commit('SET_ACTIVE_MEETINGS', [])
          commit('SET_LOADING', false)
          return []
        }

        console.log('Found meeting IDs:', response.data.meetings)

        if (response.data.meetings.length === 0) {
          console.log('Empty meetings array, returning empty list')
          commit('SET_ACTIVE_MEETINGS', [])
          commit('SET_LOADING', false)
          return []
        }

        // Fetch details for each meeting with a retry mechanism
        const meetings = []
        const fetchMeetingWithRetry = async (meetingId, retries = 2) => {
          try {
            const response = await apiClient.get(`/meetings/${meetingId}${cacheParam}`)
            console.log(`Meeting ${meetingId} detail received:`, response.data)
            // Add status information
            response.data.status = 'active'
            meetings.push(response.data)
            return response.data
          } catch (err) {
            console.error(`Error fetching meeting ${meetingId}:`, err)
            if (retries > 0) {
              console.log(`Retrying fetch for meeting ${meetingId}, ${retries} retries left`)
              await new Promise(resolve => setTimeout(resolve, 500)) // Wait 500ms before retry
              return fetchMeetingWithRetry(meetingId, retries - 1)
            }
            return null
          }
        }

        // Fetch all meetings in parallel
        const meetingPromises = response.data.meetings.map(meetingId =>
          fetchMeetingWithRetry(meetingId)
        )

        // Wait for all fetches to complete
        await Promise.all(meetingPromises)

        // Filter out any null results from failed fetches
        const validMeetings = meetings.filter(meeting => meeting !== null)

        console.log('All meetings loaded:', validMeetings)
        commit('SET_ACTIVE_MEETINGS', validMeetings)
        commit('SET_LOADING', false)
        return validMeetings
      } catch (error) {
        console.error('Error in getActiveMeetings:', error)
        commit('SET_ERROR', error.response?.data?.detail || error.message || 'Error getting active meetings')
        commit('SET_ACTIVE_MEETINGS', [])
        commit('SET_LOADING', false)
        return [] // Return empty array instead of throwing error
      }
    },
    async getNearbyMeetings({ commit, state }, { x, y }) {
      try {
        if (!state.user) {
          commit('SET_NEARBY_MEETINGS', [])
          return []
        }

        commit('SET_LOADING', true)
        const response = await apiClient.get('/meetings/nearby', {
          params: {
            email: state.user.email,
            x,
            y
          }
        })

        // Check if meetings array exists
        if (!response.data.meetings) {
          commit('SET_NEARBY_MEETINGS', [])
          commit('SET_LOADING', false)
          return []
        }

        // Fetch details for each meeting
        const meetings = []
        for (const meetingId of response.data.meetings) {
          try {
            const meetingResponse = await apiClient.get(`/meetings/${meetingId}`)
            meetings.push(meetingResponse.data)
          } catch (err) {
            console.error(`Error fetching meeting ${meetingId}:`, err)
            // Continue with other meetings if one fails
          }
        }

        commit('SET_NEARBY_MEETINGS', meetings)
        commit('SET_LOADING', false)
        return meetings
      } catch (error) {
        console.error('Error in getNearbyMeetings:', error)
        commit('SET_ERROR', error.response?.data?.detail || error.message || 'Error getting nearby meetings')
        commit('SET_NEARBY_MEETINGS', [])
        commit('SET_LOADING', false)
        throw error // re-throw the error
      }
    },
    // Participation
    async joinMeeting({ commit, state }, meetingId) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        const response = await apiClient.post(`/meetings/${meetingId}/join`, {
          email: state.user.email
        })

        if (response.data.success) {
          // Get meeting details and set as joined meeting
          const meetingResponse = await apiClient.get(`/meetings/${meetingId}`)
          commit('SET_JOINED_MEETING', meetingResponse.data)
        }

        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error joining meeting')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async leaveMeeting({ commit, state }, meetingId) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        const response = await apiClient.post(`/meetings/${meetingId}/leave`, {
          email: state.user.email
        })

        if (response.data.success) {
          commit('SET_JOINED_MEETING', null)
        }

        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error leaving meeting')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getUpcomingMeetings({ commit }, { forceRefresh = false } = {}) {
      try {
        commit('SET_LOADING', true)

        console.log(`Getting upcoming meetings... (forceRefresh=${forceRefresh})`)

        // Add a cache buster parameter for forceRefresh
        const cacheParam = forceRefresh ? `?cache=${Date.now()}` : ''

        // Call the new API endpoint for upcoming meetings
        const response = await apiClient.get(`/meetings/upcoming${cacheParam}`)
        console.log('Upcoming meetings response:', response.data)

        // Check if meetings array exists
        if (!response.data.meetings) {
          console.log('No upcoming meetings found in response')
          commit('SET_UPCOMING_MEETINGS', [])
          commit('SET_LOADING', false)
          return []
        }

        console.log('Found upcoming meeting IDs:', response.data.meetings)

        if (response.data.meetings.length === 0) {
          console.log('Empty upcoming meetings array, returning empty list')
          commit('SET_UPCOMING_MEETINGS', [])
          commit('SET_LOADING', false)
          return []
        }

        // Fetch details for each meeting with a retry mechanism
        const meetings = []
        const fetchMeetingWithRetry = async (meetingId, retries = 2) => {
          try {
            const response = await apiClient.get(`/meetings/${meetingId}${cacheParam}`)
            console.log(`Upcoming meeting ${meetingId} detail received:`, response.data)
            // Add status information
            response.data.status = 'upcoming'
            meetings.push(response.data)
            return response.data
          } catch (err) {
            console.error(`Error fetching upcoming meeting ${meetingId}:`, err)
            if (retries > 0) {
              console.log(`Retrying fetch for upcoming meeting ${meetingId}, ${retries} retries left`)
              await new Promise(resolve => setTimeout(resolve, 500)) // Wait 500ms before retry
              return fetchMeetingWithRetry(meetingId, retries - 1)
            }
            return null
          }
        }

        // Fetch all meetings in parallel
        const meetingPromises = response.data.meetings.map(meetingId =>
          fetchMeetingWithRetry(meetingId)
        )

        // Wait for all fetches to complete
        await Promise.all(meetingPromises)

        // Filter out any null results from failed fetches
        const validMeetings = meetings.filter(meeting => meeting !== null)

        console.log('All upcoming meetings loaded:', validMeetings)
        commit('SET_UPCOMING_MEETINGS', validMeetings)
        commit('SET_LOADING', false)
        return validMeetings
      } catch (error) {
        console.error('Error in getUpcomingMeetings:', error)
        commit('SET_ERROR', error.response?.data?.detail || error.message || 'Error getting upcoming meetings')
        commit('SET_UPCOMING_MEETINGS', [])
        commit('SET_LOADING', false)
        return [] // Return empty array instead of throwing error
      }
    },
    async getMeetingParticipants({ commit }, meetingId) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.get(`/meetings/${meetingId}/participants`)
        commit('SET_MEETING_PARTICIPANTS', response.data.participants)
        commit('SET_LOADING', false)
        return response.data.participants
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error getting meeting participants')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async endMeeting({ commit }, meetingId) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.post(`/meetings/${meetingId}/end`)

        if (response.data.success) {
          commit('SET_JOINED_MEETING', null)
        }

        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error ending meeting')
        commit('SET_LOADING', false)
        throw error
      }
    },
    // Chat functionality
    async postMessage({ commit, state }, { text, meetingId }) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        const response = await apiClient.post('/chat/post', {
          email: state.user.email,
          text,
          meeting_id: meetingId
        })

        commit('SET_LOADING', false)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error posting message')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getMeetingMessages({ commit }, meetingId) {
      try {
        commit('SET_LOADING', true)
        const response = await apiClient.get(`/meetings/${meetingId}/messages`)
        commit('SET_CHAT_MESSAGES', response.data.messages)
        commit('SET_LOADING', false)
        return response.data.messages
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error getting chat messages')
        commit('SET_LOADING', false)
        throw error
      }
    },
    async getUserMessages({ commit, state }, meetingId) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        const url = meetingId
          ? `/users/${state.user.email}/messages?meeting_id=${meetingId}`
          : `/users/${state.user.email}/messages`

        const response = await apiClient.get(url)
        commit('SET_USER_MESSAGES', response.data.messages)
        commit('SET_LOADING', false)
        return response.data.messages
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.error || 'Error getting user messages')
        commit('SET_LOADING', false)
        throw error
      }
    },

    async getUserCreatedMeetings({ commit, state }) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        const response = await apiClient.get(`/meetings/${state.user.email}/meetings`)

        // Get meeting IDs
        const meetingIds = response.data.meetings || [];

        if (meetingIds.length === 0) {
          commit('SET_USER_CREATED_MEETINGS', []);
          commit('SET_LOADING', false);
          return [];
        }

        // Fetch details for each meeting
        const meetings = [];
        for (const meetingId of meetingIds) {
          try {
            const meetingResponse = await apiClient.get(`/meetings/${meetingId}`);
            meetings.push(meetingResponse.data);
          } catch (err) {
            console.error(`Error fetching meeting ${meetingId}:`, err);
          }
        }

        commit('SET_USER_CREATED_MEETINGS', meetings);
        commit('SET_LOADING', false);
        return meetings;
      } catch (error) {
        console.error('Error in getUserCreatedMeetings:', error)
        commit('SET_ERROR', error.response?.data?.detail || error.message || 'Error getting user created meetings')
        commit('SET_USER_CREATED_MEETINGS', [])
        commit('SET_LOADING', false)
        return [] // Return empty array instead of throwing error
      }
    },

    async deleteMeeting({ commit, dispatch, state }, meetingId) {
      try {
        if (!state.user) {
          throw new Error('User not authenticated')
        }

        commit('SET_LOADING', true)
        await apiClient.delete(`/meetings/${meetingId}?email=${encodeURIComponent(state.user.email)}`)

        // Refresh the user's meetings after deletion
        await dispatch('getUserCreatedMeetings')

        // Also refresh active meetings list
        await dispatch('getActiveMeetings')

        commit('SET_LOADING', false)
        return true
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || error.message || 'Error deleting meeting')
        commit('SET_LOADING', false)
        throw error
      }
    },
    // Location
    setUserLocation({ commit }, location) {
      commit('SET_USER_LOCATION', location)
    },
    // Error handling
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  },
  modules: {
  }
})