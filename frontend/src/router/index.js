import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import FindMeetings from '../views/FindMeetings.vue'
import CreateMeeting from '../views/CreateMeeting.vue'
import MeetingsList from '../views/MeetingsList.vue'
import MeetingDetails from '../views/MeetingDetails.vue'
import UserProfile from '../views/UserProfile.vue'
import NotFound from '../views/NotFound.vue'
import ChatRoom from '../views/ChatRoom.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { guest: true }
  },
  {
    path: '/meetings/find',
    name: 'FindMeetings',
    component: FindMeetings,
    meta: { requiresAuth: true }
  },
  {
    path: '/meetings',
    name: 'MeetingsList',
    component: MeetingsList,
    meta: { requiresAuth: true }
  },
  {
    path: '/meetings/create',
    name: 'CreateMeeting',
    component: CreateMeeting,
    meta: { requiresAuth: true }
  },
  {
    path: '/meetings/:id',
    name: 'MeetingDetails',
    component: MeetingDetails,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-meeting',
    redirect: '/meetings/create'
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'ChatRoom',
    component: ChatRoom,
    meta: { requiresAuth: true, requiresJoinedMeeting: true }
  },
  // Fallback route - shows 404 page
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Check for auth state in local storage on first load
  if (!store.getters.isAuthenticated) {
    store.dispatch('checkAuth')
  }
  
  // Handle auth routes
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!store.getters.isAuthenticated) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
      // Check if route requires joined meeting
      if (to.matched.some(record => record.meta.requiresJoinedMeeting) && !store.getters.joinedMeeting) {
        next({ name: 'Home' })
      } else {
        next()
      }
    }
  } else if (to.matched.some(record => record.meta.guest)) {
    if (store.getters.isAuthenticated) {
      next({ name: 'Home' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router