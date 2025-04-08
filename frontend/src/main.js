import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'

// PrimeVue Theme
import 'primevue/resources/themes/lara-light-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

// PrimeVue Components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Card from 'primevue/card'
import Panel from 'primevue/panel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Toast from 'primevue/toast'
import Menubar from 'primevue/menubar'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Avatar from 'primevue/avatar'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ConfirmDialog from 'primevue/confirmdialog'
import Badge from 'primevue/badge'
import Divider from 'primevue/divider'

const app = createApp(App)

// Use PrimeVue, Router & Store
app.use(PrimeVue, { ripple: true })
app.use(ToastService)
app.use(ConfirmationService)
app.use(router)
app.use(store)

// Register PrimeVue Components
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Dropdown', Dropdown)
app.component('Calendar', Calendar)
app.component('Card', Card)
app.component('Panel', Panel)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Dialog', Dialog)
app.component('Toast', Toast)
app.component('Menubar', Menubar)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('Avatar', Avatar)
app.component('Message', Message)
app.component('ProgressSpinner', ProgressSpinner)
app.component('InputNumber', InputNumber)
app.component('Textarea', Textarea)
app.component('ConfirmDialog', ConfirmDialog)
app.component('Badge', Badge)
app.component('Divider', Divider)

// Directives
app.directive('tooltip', Tooltip)

// Mount app
app.mount('#app')