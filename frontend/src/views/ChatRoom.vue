<template>
  <div class="chat-container">
    <div v-if="!joinedMeeting" class="no-meeting">
      <Card>
        <template #title>
          <h2 class="no-meeting-title">
            <i class="pi pi-info-circle mr-2"></i>
            Not In a Meeting
          </h2>
        </template>
        <template #content>
          <div class="no-meeting-content">
            <p>You need to join a meeting to access the chat.</p>
            <div class="no-meeting-actions">
              <Button 
                label="Find a Meeting" 
                icon="pi pi-search" 
                class="p-button-success p-button-lg"
                @click="$router.push('/meetings/find')"
              />
            </div>
          </div>
        </template>
      </Card>
    </div>
    
    <div v-else class="meeting-chat">
      <Card class="chat-card">
        <template #title>
          <div class="chat-header">
            <div class="meeting-info">
              <div class="meeting-title">{{ joinedMeeting.title }}</div>
              <div class="meeting-time">{{ formatTime(joinedMeeting.t1) }} - {{ formatTime(joinedMeeting.t2) }}</div>
            </div>
            <div class="participants-info">
              <Button 
                icon="pi pi-users" 
                class="p-button-rounded p-button-text"
                @click="showParticipantsDialog = true"
                v-tooltip="'View Participants'"
              >
                <Badge :value="participants.length.toString()" class="ml-1" severity="info"></Badge>
              </Button>
            </div>
          </div>
        </template>
        <template #content>
          <div class="chat-content">
            <div class="messages-container" ref="messagesContainer">
              <div v-if="loadingMessages" class="loading-messages">
                <ProgressSpinner />
              </div>
              <div v-else-if="messages.length === 0" class="no-messages">
                <i class="pi pi-comments"></i>
                <p>No messages yet. Be the first to send a message!</p>
              </div>
              
              <div v-else class="messages">
                <div 
                  v-for="(message, index) in messages" 
                  :key="index" 
                  :class="['message', message.email === currentUser.email ? 'message-own' : 'message-other']"
                >
                  <div class="message-header">
                    <span class="message-sender">{{ message.email === currentUser.email ? 'You' : getParticipantName(message.email) }}</span>
                    <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
                  </div>
                  <div class="message-content">{{ message.message }}</div>
                </div>
              </div>
            </div>
            
            <div class="message-input">
              <div class="p-inputgroup">
                <InputText 
                  v-model="newMessage" 
                  placeholder="Type your message..." 
                  :disabled="sending"
                  @keyup.enter="sendMessage"
                />
                <Button 
                  icon="pi pi-send" 
                  @click="sendMessage"
                  :disabled="!newMessage.trim() || sending"
                  :loading="sending"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>
      
      <!-- Participants Dialog -->
      <Dialog 
        v-model:visible="showParticipantsDialog" 
        header="Meeting Participants" 
        :style="{width: '450px'}"
        modal
      >
        <div class="participants-list">
          <div v-if="loadingParticipants" class="loading-participants">
            <ProgressSpinner />
          </div>
          <div v-else-if="participants.length === 0" class="no-participants">
            <p>No participants found</p>
          </div>
          <div v-else>
            <div v-for="(participant, index) in participants" :key="index" class="participant-item">
              <Avatar 
                :label="getInitials(participant)" 
                shape="circle" 
                :style="{ backgroundColor: getAvatarColor(participant) }" 
                class="mr-2" 
              />
              <span class="participant-email">{{ participant }}</span>
              <Badge v-if="participant === currentUser.email" value="You" severity="success" />
            </div>
          </div>
        </div>
        <template #footer>
          <Button 
            label="Close" 
            icon="pi pi-times" 
            @click="showParticipantsDialog = false" 
            class="p-button-text"
          />
          <Button 
            v-if="joinedMeeting"
            label="Leave Meeting" 
            icon="pi pi-sign-out" 
            @click="confirmLeaveMeeting" 
            class="p-button-danger"
          />
        </template>
      </Dialog>
      
      <!-- Leave Meeting Confirmation Dialog -->
      <Dialog
        v-model:visible="leaveDialogVisible"
        :modal="true"
        header="Leave Meeting?"
        :style="{ width: '350px' }"
      >
        <div class="confirmation-content">
          <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
          <span>Are you sure you want to leave this meeting?</span>
        </div>
        <template #footer>
          <Button 
            label="No" 
            icon="pi pi-times" 
            @click="leaveDialogVisible = false" 
            class="p-button-text"
          />
          <Button 
            label="Yes" 
            icon="pi pi-check" 
            @click="leaveMeeting" 
            class="p-button-danger"
            :loading="leaving"
          />
        </template>
      </Dialog>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

export default {
  name: 'ChatRoom',
  setup() {
    const store = useStore();
    const router = useRouter();
    const toast = useToast();
    
    const messagesContainer = ref(null);
    const newMessage = ref('');
    const sending = ref(false);
    const leaving = ref(false);
    const loadingMessages = ref(true);
    const loadingParticipants = ref(true);
    const showParticipantsDialog = ref(false);
    const leaveDialogVisible = ref(false);
    const refreshInterval = ref(null);
    const participantNames = ref({});  // Cache for participant names
    
    const currentUser = computed(() => store.getters.currentUser);
    const joinedMeeting = computed(() => store.getters.joinedMeeting);
    const messages = computed(() => store.getters.chatMessages || []);
    const participants = computed(() => store.getters.meetingParticipants || []);
    
    onMounted(async () => {
      if (!store.getters.isAuthenticated) {
        router.push('/login');
        return;
      }
      
      if (!joinedMeeting.value) {
        return;
      }
      
      // Initial data load
      try {
        loadingMessages.value = true;
        loadingParticipants.value = true;
        
        await Promise.all([
          refreshMessages(),
          fetchParticipants()
        ]);
        
        // Start refresh interval
        startRefreshInterval();
      } catch (error) {
        console.error('Error loading chat data:', error);
      } finally {
        loadingMessages.value = false;
        loadingParticipants.value = false;
      }
    });
    
    onBeforeUnmount(() => {
      stopRefreshInterval();
    });
    
    const scrollToBottom = () => {
      nextTick(() => {
        const container = messagesContainer.value;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    };
    
    const refreshMessages = async () => {
      if (!joinedMeeting.value) return;
      
      try {
        await store.dispatch('getMeetingMessages', joinedMeeting.value.meeting_id);
        scrollToBottom();
      } catch (error) {
        console.error('Error refreshing messages:', error);
      }
    };
    
    const fetchParticipants = async () => {
      if (!joinedMeeting.value) return;
      
      try {
        await store.dispatch('getMeetingParticipants', joinedMeeting.value.meeting_id);
      } catch (error) {
        console.error('Error fetching participants:', error);
      }
    };
    
    const sendMessage = async () => {
      if (!newMessage.value.trim() || !joinedMeeting.value) return;
      
      sending.value = true;
      try {
        await store.dispatch('postMessage', {
          text: newMessage.value,
          meetingId: joinedMeeting.value.meeting_id
        });
        
        // Clear input and refresh messages
        newMessage.value = '';
        await refreshMessages();
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to send message',
          life: 3000
        });
      } finally {
        sending.value = false;
      }
    };
    
    const confirmLeaveMeeting = () => {
      showParticipantsDialog.value = false;
      leaveDialogVisible.value = true;
    };
    
    const leaveMeeting = async () => {
      if (!joinedMeeting.value) return;
      
      leaving.value = true;
      try {
        await store.dispatch('leaveMeeting', joinedMeeting.value.meeting_id);
        
        toast.add({
          severity: 'success',
          summary: 'Left Meeting',
          detail: 'You have successfully left the meeting',
          life: 3000
        });
        
        leaveDialogVisible.value = false;
        router.push('/');
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to leave meeting',
          life: 3000
        });
      } finally {
        leaving.value = false;
      }
    };
    
    const formatTime = (timeString) => {
      const date = new Date(timeString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
    
    const formatMessageTime = (timeString) => {
      const date = new Date(timeString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
    
    const getParticipantName = (email) => {
      // In a real app, we would lookup user names from a cache or server
      // For now, just return the email
      return participantNames.value[email] || email;
    };
    
    const startRefreshInterval = () => {
      // Clear any existing interval
      stopRefreshInterval();
      
      // Set up new interval (every 5 seconds)
      refreshInterval.value = setInterval(() => {
        refreshMessages();
        fetchParticipants();
      }, 5000);
    };
    
    const stopRefreshInterval = () => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value);
        refreshInterval.value = null;
      }
    };
    
    const getInitials = (email) => {
      if (!email) return '??';
      return email.substring(0, 2).toUpperCase();
    };
    
    const getAvatarColor = (email) => {
      // Generate a consistent color based on email
      if (!email) return '#CCC';
      
      let hash = 0;
      for (let i = 0; i < email.length; i++) {
        hash = email.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      const hue = hash % 360;
      return `hsl(${hue}, 70%, 60%)`;
    };
    
    return {
      messagesContainer,
      newMessage,
      showParticipantsDialog,
      leaveDialogVisible,
      sending,
      leaving,
      loadingMessages,
      loadingParticipants,
      currentUser,
      joinedMeeting,
      messages,
      participants,
      refreshMessages,
      sendMessage,
      confirmLeaveMeeting,
      leaveMeeting,
      formatTime,
      formatMessageTime,
      getParticipantName,
      getInitials,
      getAvatarColor
    };
  }
};
</script>

<style scoped>
.chat-container {
  max-width: 900px;
  margin: 0 auto;
}

.no-meeting {
  max-width: 500px;
  margin: 5rem auto;
}

.no-meeting-title {
  display: flex;
  align-items: center;
  margin: 0;
}

.no-meeting-content {
  text-align: center;
  padding: 2rem 0;
}

.no-meeting-actions {
  margin-top: 1.5rem;
}

.chat-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meeting-title {
  font-weight: bold;
  font-size: 1.2rem;
}

.meeting-time {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.chat-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background-color: var(--surface-ground);
  border-radius: 6px;
  margin-bottom: 1rem;
  position: relative;
}

.loading-messages,
.loading-participants {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.no-messages,
.no-participants {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-secondary);
  text-align: center;
}

.no-messages i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 75%;
  padding: 10px;
  border-radius: 10px;
  position: relative;
  margin-bottom: 10px;
}

.message-own {
  align-self: flex-end;
  background-color: var(--primary-color);
  color: white;
}

.message-other {
  align-self: flex-start;
  background-color: var(--surface-card);
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 0.8rem;
}

.message-own .message-header {
  color: rgba(255, 255, 255, 0.9);
}

.message-other .message-header {
  color: var(--text-color-secondary);
}

.message-sender {
  font-weight: bold;
}

.message-time {
  font-size: 0.75rem;
}

.message-content {
  word-break: break-word;
}

.message-input {
  padding-top: 0.5rem;
}

.participants-list {
  max-height: 300px;
  overflow-y: auto;
}

.participant-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--surface-border);
}

.participant-item:last-child {
  border-bottom: none;
}

.participant-email {
  font-size: 1rem;
  margin-right: auto;
}

.confirmation-content {
  display: flex;
  align-items: center;
  padding: 1rem 0;
}

.mr-2 {
  margin-right: 0.5rem;
}

.mr-3 {
  margin-right: 0.75rem;
}

.ml-1 {
  margin-left: 0.25rem;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .chat-card {
    height: calc(100vh - 160px);
  }
  
  .message {
    max-width: 90%;
  }
  
  .no-meeting {
    margin: 2rem auto;
  }
}
</style>