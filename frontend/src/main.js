import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, TitleComponent,
  LegendComponent, DataZoomComponent
} from 'echarts/components'

import router from './router'
import App from './App.vue'
import './style.css'

use([CanvasRenderer, BarChart, ScatterChart,
     GridComponent, TooltipComponent, TitleComponent,
     LegendComponent, DataZoomComponent])

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { size: 'default' })
app.component('VChart', VChart)

for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp)
}

app.mount('#app')
