<template>
  <div class="page">
    <nav class="nav">
      <div class="brand" @click="router.push('/oc')">
        <span class="logo-icon">🎭</span> OC 一键求职
      </div>
      <div class="links">
        <router-link to="/oc" class="link active">OC 求职</router-link>
      </div>
    </nav>

    <div class="content">
      <!-- 左侧：操作与列表 -->
      <div class="sidebar">
        <!-- 简历生成面板 -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-icon">🧬</div>
            <div class="panel-title-group">
              <div class="h1">简历生成</div>
              <div class="hint">上传设定档案，生成专业简历</div>
            </div>
          </div>

          <div class="form">
            <div class="form-group">
              <div class="row">
                <label class="lab">目标岗位</label>
                <input class="inp" v-model="targetRole" placeholder="如：前端工程师" />
              </div>
              <div class="row">
                <label class="lab">目标级别</label>
                <input class="inp" v-model="targetLevel" placeholder="如：P6 / 资深" />
              </div>
            </div>

            <div class="sample-area">
              <div class="sample-header">
                <div class="sample-title">一键体验样例</div>
                <div class="sample-subtitle">选择预设角色，立即体验完整流程</div>
              </div>
              <div class="sample-grid">
                <button class="sample-card primary" @click="useSample(sampleCases[0])">
                  <div class="sample-bg-effect"></div>
                  <div class="sample-content">
                    <div class="sample-name">{{ sampleCases[0].name }}</div>
                    <div class="sample-desc">{{ sampleCases[0].desc }}</div>
                    <div class="sample-cta">⚡ 点击加载角色档案</div>
                  </div>
                </button>
              </div>
            </div>

            <div class="upload-box" @click="$refs.fileInput.click()">
              <input ref="fileInput" class="inp-file" type="file" @change="onPickFile" accept=".pdf,.txt,.md" hidden />
              <div class="upload-inner" v-if="!pickedFile">
                <div class="upload-icon">📂</div>
                <div class="upload-text">点击上传设定文件 (PDF/TXT/MD)</div>
                <div class="upload-sub">支持小说大纲、角色小传</div>
              </div>
              <div class="upload-file" v-else>
                <span class="file-icon">📜</span>
                <span class="file-name">{{ pickedFile.name }}</span>
                <span class="file-status">已就绪</span>
              </div>
            </div>

            <div class="role-select" v-if="roleOptions.length">
              <div class="role-select-title">识别到多个角色，请选择要生成的角色</div>
              <div class="role-options">
                <button class="role-option"
                        v-for="r in roleOptions"
                        :key="r.name"
                        :class="{ active: selectedRole === r.name }"
                        @click="selectedRole = r.name">
                  <div class="role-name">{{ r.name }}</div>
                  <div class="role-summary" v-if="r.summary">{{ r.summary }}</div>
                </button>
              </div>
            </div>

            <div class="actions">
              <button class="btn primary full glitch-effect" :disabled="!pickedFile || loading" @click="onGenerate">
                <span v-if="loading" class="spinner"></span>
                <span v-else>{{ roleOptions.length ? '确认角色 · 开始生成' : '开始生成简历' }}</span>
              </button>
            </div>
            <div class="actions" v-if="resume">
               <button class="btn ghost full" @click="onPrint">🖨️ 导出简历 (PDF)</button>
            </div>
          </div>
        </div>

        <!-- 投递与沟通面板 -->
        <div class="panel flex-1" v-if="resumeId">
          <div class="panel-header">
             <div class="panel-icon">🚀</div>
             <div class="panel-title-group">
              <div class="h1">求职中心</div>
              <div class="hint">投递公司，模拟真实沟通</div>
            </div>
          </div>

          <div class="tabs-control">
            <button class="tab-btn" :class="{ active: sidebarTab === 'companies' }" @click="sidebarTab = 'companies'">职位广场</button>
            <button class="tab-btn" :class="{ active: sidebarTab === 'applications' }" @click="sidebarTab = 'applications'">
              投递记录 <span class="badge-count" v-if="applications.length">{{ applications.length }}</span>
            </button>
          </div>

          <div class="list-scroll" v-if="sidebarTab === 'companies'">
            <div class="company-card" v-for="c in companies" :key="c.id">
              <div class="company-logo" :style="{ background: getCompanyColor(c.name) }">{{ c.name[0] }}</div>
              <div class="company-info">
                <div class="company-name">{{ c.name }}</div>
                <div class="company-meta">{{ c.industry }} · {{ (c.open_roles || []).slice(0, 2).join('/') }}</div>
              </div>
              <button class="btn-apply"
                      :class="{ applied: appliedCompanyIds.has(c.id) }"
                      :disabled="loadingApply"
                      @click="onStartChat(c.id)">
                {{ appliedCompanyIds.has(c.id) ? '继续沟通' : '立即沟通' }}
              </button>
            </div>
          </div>

          <div class="list-scroll" v-else>
            <div class="app-card"
                 v-for="a in applications"
                 :key="a.id"
                 :class="{ selected: selectedApplicationId === a.id }"
                 @click="selectApplication(a)">
              <div class="app-header">
                <div class="company-logo small" :style="{ background: getCompanyColor(a.company_name) }">{{ a.company_name[0] }}</div>
                <div class="app-info">
                  <div class="app-company-name">{{ a.company_name }}</div>
                  <div class="app-contact">
                    <span class="role-tag">{{ a.contact_type === 'headhunter' ? '猎头' : 'HR' }}</span>
                    <span class="time-ago">{{ formatTime(a.updated_at) }}</span>
                  </div>
                </div>
                <div class="app-status-badge" :class="getStatusClass(a.status)">{{ getStatusText(a.status) }}</div>
              </div>
            </div>
             <div class="empty-state" v-if="!applications.length">暂无投递记录</div>
          </div>
        </div>
      </div>

      <!-- 右侧：主内容区 -->
      <div class="main-view">
        <div class="view-tabs" v-if="resume">
          <button class="view-tab" :class="{ active: activeTab === 'resume' }" @click="activeTab = 'resume'">
            <span class="icon">📄</span> 简历预览
          </button>
          <button class="view-tab" :class="{ active: activeTab === 'chat' }" @click="activeTab = 'chat'">
            <span class="icon">💬</span> 沟通消息
             <span class="badge-dot" v-if="applications.length"></span>
          </button>
        </div>

        <div class="view-content" v-if="resume && activeTab === 'resume'">
          <div class="preview-scroll">
            <OcResumePreview :resume="resume" />
          </div>
        </div>

        <div class="view-content chat-mode" v-if="resume && activeTab === 'chat'">
          <div class="chat-container" v-if="selectedApplication">
            <div class="chat-header">
              <div class="chat-avatar-wrap">
                 <div class="company-logo medium" :style="{ background: getCompanyColor(selectedApplication.company_name) }">
                   {{ selectedApplication.company_name[0] }}
                 </div>
                 <div class="online-dot"></div>
              </div>
              <div class="chat-header-info">
                <div class="chat-name">{{ selectedApplication.company_name }} {{ selectedApplication.contact_type === 'headhunter' ? '猎头' : 'HR' }}</div>
                <div class="chat-status">
                  <span class="status-indicator">●</span> 对方正在输入... | 好感度: {{ Math.floor(Math.random() * 20) + 80 }}%
                </div>
              </div>
              <div class="chat-actions">
                 <button class="icon-btn" title="查看企业档案">🏢</button>
                 <button class="icon-btn" title="更多操作">⋮</button>
              </div>
            </div>

            <!-- Job Card (Boss Style) -->
            <div class="chat-job-card">
              <div class="job-card-main">
                <div class="job-card-title">{{ selectedApplication.role || '意向职位' }}</div>
                <div class="job-card-salary">薪资面议</div>
              </div>
              <div class="job-card-sub">{{ selectedApplication.company_name }} · {{ selectedApplication.contact_type === 'headhunter' ? '猎头' : 'HR' }}招聘</div>
            </div>

            <div class="chat-messages" ref="chatBodyRef">
              <TransitionGroup name="message-anim">
                <div class="message-group" v-for="(m, idx) in chatMessages" :key="m.ts + idx" :class="m.role">
                  <div class="message-avatar" v-if="m.role === 'assistant'">
                     <div class="company-logo xs" :style="{ background: getCompanyColor(selectedApplication.company_name) }">{{ selectedApplication.company_name[0] }}</div>
                  </div>
                  <div class="message-content">
                    <div class="bubble">{{ m.content }}</div>
                    <div class="message-meta">
                      <span class="message-read" v-if="m.role === 'user'">已读</span>
                      <span class="message-time">{{ formatTime(m.ts) }}</span>
                    </div>
                  </div>
                  <div class="message-avatar" v-if="m.role === 'user'">
                     <div class="user-avatar">我</div>
                  </div>
                </div>
              </TransitionGroup>
              <div class="typing-indicator" v-if="chatLoading">
                <span></span><span></span><span></span>
              </div>
            </div>

            <div class="chat-input-area">
              <div class="chat-tools">
                <button class="tool-btn" @click="sendAction('resume')">📄 发送简历</button>
                <button class="tool-btn" @click="sendAction('wechat')">📱 交换微信</button>
                <button class="tool-btn" @click="onAutoReply">🎭 角色续聊</button>
                <button class="tool-btn" @click="sendAction('phone')">📞 交换电话</button>
              </div>
              <div class="chat-input-row">
                <input class="chat-inp"
                       v-model="chatInput"
                       :disabled="chatLoading"
                       placeholder="新招呼..."
                       @keydown.enter.prevent="onSendChat" />
                <button class="btn-send" :disabled="!chatInput.trim() || chatLoading" @click="onSendChat">
                  <span class="send-icon">➤</span>
                </button>
              </div>
            </div>
          </div>
          
          <div class="empty-chat" v-else>
            <div class="empty-icon">💬</div>
            <div class="empty-text">请在左侧选择一个投递记录开始沟通</div>
          </div>
        </div>

        <div class="empty-main" v-if="!resume">
          <div class="empty-illustration">📄</div>
          <div class="empty-title">等待简历生成</div>
          <div class="empty-desc">请在左侧上传设定文件，AI 将为您生成专业简历</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import toast from '../utils/toast'
import { generateOcResumeFromFile, listCompanies, applyToCompany, listApplications, getChatHistory, sendChatMessage } from '../api/recruit'
import OcResumePreview from '../components/OcResumePreview.vue'
import { sampleResume, sampleCompanies, sampleApplications, sampleChat, sampleChatMap } from '../data/sampleOc'

const router = useRouter()

const loading = ref(false)
const pickedFile = ref(null)
const resume = ref(null)
const resumeId = ref('')
const extractedPreview = ref('')
const companies = ref([])
const applications = ref([])
const loadingApply = ref(false)
const activeTab = ref('resume')
const sidebarTab = ref('companies') // companies | applications
const selectedApplicationId = ref('')
const selectedApplication = computed(() => (applications.value || []).find(a => a.id === selectedApplicationId.value) || null)
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBodyRef = ref(null)
const localChatMap = ref({})

const targetRole = ref('')
const targetLevel = ref('')
const roleOptions = ref([])
const selectedRole = ref('')
const sampleCases = [
  {
    id: 'wuxia-pure-swordsman',
    name: '武侠穿越 · 孤城问剑',
    desc: '白云城主叶孤城，以纯粹剑客身份，向互联网大厂发起挑战',
    text: `《陆小凤传奇》
角色：叶孤城
身份：白云城主
性格：孤高冷傲，目空一切，视剑如命
经历：
1. 居南海飞仙岛，练剑二十载，剑法已臻化境。
2. 曾与西门吹雪约战紫禁之巅，一剑西来，天外飞仙。
3. 生平未尝一败，只求一敌。
技能：
1. 天外飞仙：辉煌至极的剑法，人剑合一。
2. 听声辨位：风吹草动，皆在掌握。
3. 绝顶轻功：来去无踪，踏雪无痕。
偏好：寻找能接我一剑的对手，不屑与凡夫俗子为伍。
目标方向：寻找最强对手 / 剑道巅峰`
  }
]

const onPickFile = (e) => {
  const f = e.target.files && e.target.files[0]
  pickedFile.value = f || null
  resume.value = null
  resumeId.value = ''
  extractedPreview.value = ''
  roleOptions.value = []
  selectedRole.value = ''
  applications.value = []
  selectedApplicationId.value = ''
  localChatMap.value = {}
}

const useSample = async (sample) => {
  if (!sample || loading.value) return

  // 演示模式：直接加载硬编码数据，跳过后端 API 调用
  if (sample.id === 'wuxia-pure-swordsman') {
    loading.value = true
    setTimeout(() => {
      resume.value = sampleResume
      resumeId.value = 'sample-resume-id'
      extractedPreview.value = '（演示模式：已自动加载《陆小凤传奇》叶孤城的设定数据...）'
      companies.value = sampleCompanies
      applications.value = sampleApplications
      localChatMap.value = {}
      selectedApplicationId.value = ''
      
      // 默认选中第一个投递记录并加载聊天
      if (applications.value.length > 0) {
        selectedApplicationId.value = applications.value[0].id
        chatMessages.value = sampleChatMap[selectedApplicationId.value] || sampleChat
      }
      
      loading.value = false
      activeTab.value = 'chat'
      toast.success('已加载演示数据，请体验求职交互')
    }, 800)
    return
  }

  const file = new File([sample.text], `${sample.id}.txt`, { type: 'text/plain' })
  pickedFile.value = file
  resume.value = null
  resumeId.value = ''
  extractedPreview.value = ''
  roleOptions.value = []
  selectedRole.value = ''
  applications.value = []
  await onGenerate()
}

const onGenerate = async () => {
  if (!pickedFile.value) return
  loading.value = true
  try {
    const res = await generateOcResumeFromFile(pickedFile.value, {
      target_role: targetRole.value || '不限',
      target_level: targetLevel.value || '不限',
      selected_role: selectedRole.value || ''
    })
    const payload = res.data || {}
    if (payload.requires_role_select && Array.isArray(payload.roles) && payload.roles.length) {
      roleOptions.value = payload.roles
      selectedRole.value = payload.roles[0]?.name || ''
      toast.info('检测到多个角色，请选择后继续生成')
      return
    }
    resume.value = payload.resume || null
    resumeId.value = payload.resume_id || ''
    extractedPreview.value = payload.extracted_text_preview || ''
    roleOptions.value = []
    selectedRole.value = ''
    toast.success('简历已生成')
    await refreshRecruit()
    await ensureAutoApplications()
    sidebarTab.value = 'applications'
  } catch (e) {
    resume.value = null
    resumeId.value = ''
  } finally {
    loading.value = false
  }
}

const refreshRecruit = async () => {
  if (!resumeId.value) return
  const [cs, apps] = await Promise.all([
    listCompanies(),
    listApplications({ resume_id: resumeId.value })
  ])
  const profile = buildPersonaProfile()
  companies.value = (cs.data || []).map((c, index) => ({
    ...c,
    style: resolveCompanyStyle(profile, c, index)
  }))
  applications.value = apps.data || []
}

const appliedCompanyIds = computed(() => new Set((applications.value || []).map(a => a.company_id || a.companyId)))

const onStartChat = async (companyId) => {
  if (!resumeId.value) {
    toast.error('请先生成简历')
    return
  }
  
  // Check if already applied
  const existingApp = applications.value.find(a => a.companyId === companyId || a.company_id === companyId)
  
  if (existingApp) {
    selectApplication(existingApp)
    sidebarTab.value = 'applications'
    return
  }

  // New Application (Start Chat)
  // 演示模式：前端模拟投递
  if (resumeId.value === 'sample-resume-id') {
    loadingApply.value = true
    setTimeout(() => {
       const company = companies.value.find(c => c.id === companyId)
       const newApp = {
         id: `app_${Date.now()}`,
         companyId: companyId,
         companyName: company.name,
         company_name: company.name,
         companyLogo: company.logo,
         role: company.openPositions[0],
         status: 'pending', // "新招呼"
         contact_type: 'hr',
         appliedAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
         updated_at: new Date().toISOString(),
         timeline: [{ status: 'pending', time: new Date().toISOString(), desc: '发起沟通' }]
       }
       applications.value.unshift(newApp)
       toast.success('已发起沟通')
       loadingApply.value = false
       sidebarTab.value = 'applications'
       
       // Auto select and send greeting
       selectApplication(newApp)
       
       // Send default greeting
       const greeting = `您好，我对贵公司的 ${newApp.role} 职位很感兴趣，希望能进一步了解。`
       chatInput.value = greeting
       onSendChat()
    }, 500)
    return
  }

  loadingApply.value = true
  try {
    const res = await applyToCompany({ resume_id: resumeId.value, company_id: companyId })
    toast.success('已发起沟通')
    await refreshRecruit()
    sidebarTab.value = 'applications' // 投递后自动切换到记录
    
    // Auto select newly created application
    // Assuming refreshRecruit updates applications list, we find the new one
    const newApp = applications.value.find(a => a.company_id === companyId || a.companyId === companyId)
    if (newApp) {
      selectApplication(newApp)
      // Send default greeting
      const greeting = `您好，我对贵公司的 ${newApp.role || '该'} 职位很感兴趣，希望能进一步了解。`
      chatInput.value = greeting
      onSendChat() 
    }
  } finally {
    loadingApply.value = false
  }
}

// Deprecated: onApply replaced by onStartChat
const onApply = async (companyId) => {
  // ... kept for reference if needed, but onStartChat covers it
  onStartChat(companyId)
}

const selectApplication = async (app) => {
  selectedApplicationId.value = app.id
  activeTab.value = 'chat'
  await loadChatHistory()
}

const loadChatHistory = async () => {
  if (!selectedApplicationId.value) return
  
  if (resumeId.value === 'sample-resume-id') {
    chatMessages.value = sampleChatMap[selectedApplicationId.value] || sampleChat
    scrollToBottom()
    return
  }

  if (selectedApplication.value?.local_only) {
    chatMessages.value = localChatMap.value[selectedApplicationId.value] || []
    scrollToBottom()
    return
  }

  const res = await getChatHistory({ application_id: selectedApplicationId.value })
  chatMessages.value = res.data?.messages || []
  scrollToBottom()
}

const onSendChat = async () => {
  if (!selectedApplicationId.value) return
  const text = chatInput.value.trim()
  if (!text) return
  chatInput.value = ''
  chatLoading.value = true
  const now = Math.floor(Date.now() / 1000)
  if (resumeId.value === 'sample-resume-id') {
    chatMessages.value = [...chatMessages.value, { role: 'user', content: text, ts: now }]
    scrollToBottom()
    setTimeout(() => {
      const reply = "（演示回复）非常有意思！您的经历确实非常独特。除了技术方面，您在团队协作中遇到过最大的挑战是什么？"
      chatMessages.value = [...chatMessages.value, { role: 'assistant', content: reply, ts: Math.floor(Date.now() / 1000) }]
      scrollToBottom()
      chatLoading.value = false
    }, 1000)
    return
  }

  if (selectedApplication.value?.local_only) {
    const current = localChatMap.value[selectedApplicationId.value] || []
    const next = [...current, { role: 'user', content: text, ts: now }]
    localChatMap.value = { ...localChatMap.value, [selectedApplicationId.value]: next }
    chatMessages.value = next
    scrollToBottom()
    setTimeout(() => {
      const reply = buildHrAutoReply(buildPersonaProfile(), selectedApplication.value, text)
      const after = [...(localChatMap.value[selectedApplicationId.value] || next), { role: 'assistant', content: reply, ts: Math.floor(Date.now() / 1000) }]
      localChatMap.value = { ...localChatMap.value, [selectedApplicationId.value]: after }
      chatMessages.value = after
      scrollToBottom()
      chatLoading.value = false
    }, 800)
    return
  }

  chatMessages.value = [...chatMessages.value, { role: 'user', content: text, ts: now }]
  scrollToBottom()
  
  try {
    const res = await sendChatMessage({ application_id: selectedApplicationId.value, message: text })
    const reply = res.data?.message || ''
    chatMessages.value = [...chatMessages.value, { role: 'assistant', content: reply, ts: Math.floor(Date.now() / 1000) }]
    scrollToBottom()
  } finally {
    chatLoading.value = false
  }
}

const sendAction = (type) => {
  let text = ''
  if (type === 'resume') {
    text = '我向您发送了在线简历，请查收。'
  } else if (type === 'wechat') {
    text = '您好，方便交换一下微信吗？希望能更深入地沟通。'
  } else if (type === 'phone') {
    text = '您好，方便交换一下联系电话吗？'
  }
  
  if (text) {
    chatInput.value = text
    onSendChat()
  }
}

const getLastAssistantMessage = () => {
  const list = chatMessages.value || []
  for (let i = list.length - 1; i >= 0; i--) {
    if (list[i]?.role === 'assistant') return list[i]?.content || ''
  }
  return ''
}

const buildCandidateAutoReply = (profile, app, lastHr) => {
  const role = app?.role || '该岗位'
  const companyName = app?.company_name || app?.companyName || '贵司'
  const key = pickKeyStrength(profile)
  const title = profile.title ? `，${profile.title}` : ''
  const text = lastHr || ''
  const tone = profile.tone
  if (tone === 'wuxia') {
    if (/薪资|待遇|钱|报酬|银/.test(text)) return '银两可议，重在对手与规矩。若合意，愿听差遣。'
    if (/时间|面试|方便|到岗/.test(text)) return '近来皆可。若要一战，随时可赴。'
    if (/简历|材料|作品|项目/.test(text)) return '在下过往事迹尽录，可再呈上。'
    return `在下${profile.name || '无名'}，愿以${key}之长相助${companyName}${role}，若有考校，尽管放马过来。`
  }
  if (/薪资|待遇|钱|报酬|期望/.test(text)) return '薪资可根据岗位级别与职责匹配度再细聊，我更关注成长空间与业务挑战。'
  if (/时间|面试|方便|到岗/.test(text)) return '本周内均可安排沟通，时间上比较灵活。'
  if (/简历|材料|作品|项目/.test(text)) return `我可以补充相关项目材料，也愿详细说明${key}经历。`
  if (/为什么|动机|原因|兴趣/.test(text)) return `主要是看重${companyName}在该方向的积累，也希望把我的${key}能力放在更有挑战的场景。`
  return `您好，我是${profile.name}${title}。对${companyName}${role}很感兴趣，也愿进一步说明我的${key}经历。`
}

const onAutoReply = () => {
  if (!selectedApplicationId.value) return
  const profile = buildPersonaProfile()
  const app = selectedApplication.value || {}
  const lastHr = getLastAssistantMessage()
  const reply = buildCandidateAutoReply(profile, app, lastHr)
  if (!reply) return
  chatInput.value = reply
  onSendChat()
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

const onPrint = () => {
  window.print()
}

// Helpers
const buildPersonaProfile = () => {
  const basics = resume.value?.basics || {}
  const summary = resume.value?.summary || ''
  const tags = Array.isArray(resume.value?.tags) ? resume.value.tags.filter(Boolean) : []
  const skills = Array.isArray(resume.value?.skills) ? resume.value.skills : []
  const skillText = skills.flatMap(s => Array.isArray(s.items) ? s.items : []).join(' ')
  const seed = `${extractedPreview.value || ''} ${summary} ${tags.join(' ')} ${skillText}`
  const isWuxia = /江湖|剑|侠|掌门|门派|宗门|轻功|内功|天机|飞仙|刀|枪|武/.test(seed)
  const name = (basics.name || '').trim() || '候选人'
  const title = (basics.title || '').trim()
  return { name, title, summary, tags, skillText, tone: isWuxia ? 'wuxia' : 'normal' }
}

const buildStrengthPool = (profile) => {
  const tags = Array.isArray(profile.tags) ? profile.tags.filter(Boolean) : []
  const skills = (profile.skillText || '').split(/\s+/).filter(Boolean)
  const summaryParts = (profile.summary || '').split(/[,，。；;、/]/).map(s => s.trim()).filter(Boolean)
  const pool = [...tags, ...skills, ...summaryParts].filter(Boolean)
  const unique = []
  const seen = new Set()
  for (const item of pool) {
    if (!seen.has(item)) {
      unique.push(item)
      seen.add(item)
    }
  }
  if (unique.length) return unique
  return profile.tone === 'wuxia'
    ? ['剑术', '轻功', '内功', '实战', '江湖阅历']
    : ['项目推进', '沟通协作', '问题分析', '执行力', '学习能力']
}

const resolveCompanyStyle = (profile, company, index) => {
  if (company?.style) return company.style
  const normalPool = ['startup', 'trendy', 'serious', 'professional', 'normal']
  const tone = company?.tone || ''
  const industry = company?.industry || ''
  if (/谨慎|严谨|合规|可靠|工程/.test(tone + industry)) return 'serious'
  if (/结果|指标|专业|克制/.test(tone + industry)) return 'professional'
  if (/热情|直接|看作品|快|游戏/.test(tone + industry)) return 'startup'
  if (/轻松|友好|表达|内容|社区/.test(tone + industry)) return 'trendy'
  return normalPool[index % normalPool.length]
}

const pickKeyStrength = (profile) => {
  const tag = profile.tags?.find(Boolean)
  if (tag) return tag
  const skill = (profile.skillText || '').split(' ').find(Boolean)
  if (skill) return skill
  const summaryMatch = (profile.summary || '').split(/[,，。；;]/).find(Boolean)
  return summaryMatch || '相关经历'
}

const buildCandidateIntro = (profile, role, companyName, style) => {
  if (profile.tone === 'wuxia') {
    const who = profile.name && profile.name !== '候选人' ? `在下${profile.name}` : '在下无名剑客'
    if (style === 'wuxia_mysterious') return `${who}，听闻贵楼知晓天下事。特来投奔，愿以手中长剑换一个真相。`
    if (style === 'wuxia_official') return `${who}，愿为朝廷效力，护一方平安。`
    if (style === 'wuxia_business') return `${who}，虽是江湖人，也懂几分规矩。愿护贵号商路畅通。`
    return `${who}，闻${companyName}征募${role || '此职'}，愿以一身所学应之。若问长短，唯有一剑止纷争。`
  }
  
  const title = profile.title ? `，${profile.title}` : ''
  if (style === 'startup') return `Hi，我是${profile.name}。看你们JD挺有意思，我也喜欢扁平化和快节奏，聊聊？`
  if (style === 'trendy') return `哈喽，我是${profile.name}！一直关注${companyName}的内容，感觉脑洞很大，想加入一起搞事情！✨`
  if (style === 'serious') return `您好，我是${profile.name}${title}。我对贵司在${role || '该领域'}的专业度印象深刻，希望能有机会交流。`
  if (style === 'professional') return `您好，我是${profile.name}${title}。对贵司${role || '该岗位'}很感兴趣，相信我的${pickKeyStrength(profile)}经验能带来价值。`

  return `您好，我是${profile.name}${title}。看到贵司${role || '该岗位'}，与我经历匹配度较高，想进一步了解。`
}

const buildHrGreeting = (profile, role, companyName, style, keyStrength) => {
  const key = keyStrength || pickKeyStrength(profile)
  
  if (style === 'startup') return `Hey！看到你简历上写了${key}，感觉很Hardcore啊！我们团队都是年轻人，要不要来面基一下？🚀`
  if (style === 'trendy') return `宝子！你的${key}经历太戳我了！😍 我们正缺这样一个${role}，快来加入我们！`
  if (style === 'serious') return `您好，这里是${companyName}人事部。经评估您的${key}经验符合我司${role}岗位要求，现邀请您进行初步沟通。`
  if (style === 'professional') return `您好，${companyName}正在寻找${role}。鉴于您在${key}领域的积累，我们认为您是极佳的人选。`

  return `您好，这里是${companyName}招聘${role || '相关岗位'}。看到您的简历，想了解您在${key}方面的经历，方便聊聊吗？`
}

const buildHrFollowup = (profile, style) => {
  if (style === 'startup') return 'Nice！那啥，咱们这儿虽然累点但成长快（也可能是大饼）。你期望薪资大概多少？下周能来搬砖不？'
  if (style === 'trendy') return '太棒惹！👏 那薪资方面有什么小目标吗？什么时候能来玩？'
  if (style === 'serious') return '收到。请问您的期望薪资范围是多少？最快到岗时间？'
  
  return '感谢说明。方便补充一下期望薪资和可面试时间吗？'
}

const buildHrAutoReply = (profile, app, userText) => {
  const style = app.style || 'normal'
  if (/薪资|待遇|钱/.test(userText)) {
    if (style === 'startup') return '期权给够！现金咱们可以再聊，主要是看能力！'
    if (style === 'trendy') return '薪资包满意的！只要活好，老板超大方！💰'
    if (style === 'serious') return '我们会根据职级体系定薪。请提供目前的薪资证明。'
    return '薪资可面议。方便告知期望范围和到岗时间吗？'
  }
  
  if (/时间|面试|方便/.test(userText)) {
    if (style === 'startup') return '今晚就可以！或者周末也行，我们随时都在！'
    if (style === 'serious') return '请等待HRBP的电话通知，我们会安排统一面试。'
    return '感谢说明。我们这边可安排面试，您近期哪天方便？'
  }
  
  return '收到，我们继续评估匹配度，方便补充期望薪资与到岗时间吗？'
}

const buildFallbackCompanies = (profile) => {
  return [
    { id: 'auto_star', name: '星河智联', industry: '科技', style: 'startup', open_roles: ['产品运营', '项目协调', '客户成功'] },
    { id: 'auto_dawn', name: '晨岚传媒', industry: '内容', style: 'trendy', open_roles: ['内容策划', '品牌合作', '编辑'] },
    { id: 'auto_forge', name: '北辰制造', industry: '制造', style: 'serious', open_roles: ['供应链专员', '流程优化', '现场管理'] },
    { id: 'auto_spring', name: '春潮教育', industry: '教育', style: 'gentle', open_roles: ['课程运营', '教研助理', '用户增长'] },
    { id: 'auto_mountain', name: '群峰咨询', industry: '咨询', style: 'professional', open_roles: ['研究助理', '交付支持', '项目跟进'] }
  ]
}

const buildAutoApplications = () => {
  const profile = buildPersonaProfile()
  const baseCompanies = (companies.value && companies.value.length) ? companies.value : buildFallbackCompanies(profile)
  const existing = applications.value || []
  const usedKeys = new Set(existing.map(a => `${a.company_id || a.companyId || a.company_name || a.companyName}`))
  const targetCount = 5
  const need = Math.max(0, targetCount - existing.length)
  if (!need) return []
  const strengthPool = buildStrengthPool(profile)
  const statuses = ['applied', 'interview', 'applied', 'offer', 'rejected']
  const newApps = []
  let idx = 0
  while (newApps.length < need) {
    const company = baseCompanies[idx % baseCompanies.length]
    const companyId = company.id || `auto_company_${idx}`
    const companyName = company.name || `未知公司${idx + 1}`
    const style = resolveCompanyStyle(profile, company, idx)
    const key = usedKeys.has(companyId) || usedKeys.has(companyName) ? `${companyId}_${newApps.length}` : companyId
    usedKeys.add(key)
    const roles = company.open_roles || company.openPositions || company.roles || []
    const role = roles[idx % (roles.length || 1)] || (profile.tone === 'wuxia' ? ['护卫', '教习', '镖师', '巡行使', '外勤统领'][idx % 5] : ['运营', '产品', '项目协调', '客户成功', '内容策划'][idx % 5])
    const now = new Date(Date.now() - (idx + 1) * 3600 * 1000)
    const app = {
      id: `auto_app_${resumeId.value}_${Date.now()}_${idx}`,
      company_id: companyId,
      companyId: companyId,
      company_name: companyName,
      companyName: companyName,
      role,
      status: statuses[idx % statuses.length],
      contact_type: idx % 2 === 0 ? 'hr' : 'headhunter',
      appliedAt: now.toISOString(),
      updatedAt: now.toISOString(),
      updated_at: now.toISOString(),
      local_only: true,
      style,
      key_strength: strengthPool[idx % strengthPool.length] || pickKeyStrength(profile),
      timeline: [{ status: statuses[idx % statuses.length], time: now.toISOString(), desc: '自动投递' }]
    }
    newApps.push(app)
    idx += 1
  }
  const nowTs = Math.floor(Date.now() / 1000)
  newApps.forEach((app, index) => {
    const companyName = app.company_name
    const initialMessages = [
      { role: 'assistant', content: buildHrGreeting(profile, app.role, companyName, app.style, app.key_strength), ts: nowTs - 600 - index * 20 },
      { role: 'user', content: buildCandidateIntro(profile, app.role, companyName, app.style), ts: nowTs - 520 - index * 20 },
      { role: 'assistant', content: buildHrFollowup(profile, app.style), ts: nowTs - 440 - index * 20 }
    ]
    localChatMap.value = { ...localChatMap.value, [app.id]: initialMessages }
  })
  return newApps
}

const ensureAutoApplications = async () => {
  if (!resume.value) return
  const newApps = buildAutoApplications()
  if (newApps.length) {
    applications.value = [...newApps, ...(applications.value || [])]
  }
  if (!selectedApplicationId.value && applications.value.length) {
    selectedApplicationId.value = applications.value[0].id
    // 保持在简历页，不自动跳转聊天
    // activeTab.value = 'chat'
    await loadChatHistory()
  }
}

const getCompanyColor = (name) => {
  const colors = ['#FF5722', '#2196F3', '#009688', '#9C27B0', '#3F51B5', '#E91E63', '#607D8B', '#FF9800']
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const formatTime = (ts) => {
  if (!ts) return ''
  // Handle ISO string or timestamp (seconds)
  let date
  if (typeof ts === 'string') {
    date = new Date(ts)
  } else {
    date = new Date(ts * 1000)
  }
  
  if (isNaN(date.getTime())) return ''

  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getStatusText = (status) => {
  const map = { 'applied': '已投递', 'interview': '面试中', 'offer': '录用', 'rejected': '不匹配' }
  return map[status] || status
}

const getStatusClass = (status) => {
  return `status-${status}`
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.page {
  min-height: 100vh;
  background: #121214;
  color: #E0E0E0;
  font-family: 'Inter', -apple-system, sans-serif;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.nav {
  height: 60px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #27272A;
  background: #18181B;
  flex-shrink: 0;
}

.brand {
  font-weight: 800;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  letter-spacing: -0.5px;
}

.links {
  display: flex;
  gap: 8px;
}

.link {
  color: #A1A1AA;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.link:hover {
  background: #27272A;
  color: #fff;
}

.link.active {
  background: #fff;
  color: #000;
}

/* Layout */
.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 400px;
  background: #18181B;
  border-right: 1px solid #27272A;
  display: flex;
  flex-direction: column;
  gap: 1px; /* Divider */
  position: relative;
  z-index: 5;
}

.main-view {
  flex: 1;
  background: #09090B;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Panel */
.panel {
  display: flex;
  flex-direction: column;
  background: #18181B;
  padding: 20px;
  gap: 16px;
}

.panel.flex-1 {
  flex: 1;
  min-height: 0;
  padding-bottom: 0;
}

.panel-header {
  display: flex;
  gap: 12px;
  align-items: center;
}

.panel-icon {
  width: 36px;
  height: 36px;
  background: #27272A;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.h1 {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.hint {
  font-size: 12px;
  color: #71717A;
}

/* Form */
.form-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.lab {
  font-size: 11px;
  font-weight: 700;
  color: #71717A;
  margin-bottom: 4px;
  display: block;
}

.inp {
  width: 100%;
  height: 36px;
  background: #27272A;
  border: 1px solid #3F3F46;
  border-radius: 6px;
  padding: 0 10px;
  color: #fff;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.inp:focus {
  border-color: #52525B;
}

.upload-box {
  border: 2px dashed #3F3F46;
  border-radius: 8px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #202023;
  gap: 8px;
}

.upload-box:hover {
  border-color: #71717A;
  background: #27272A;
}

.upload-text {
  font-size: 12px;
  color: #71717A;
  font-weight: 500;
}

.sample-area {
  margin-top: 12px;
  background: #1B1B1F;
  border: 1px solid #2A2A2E;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sample-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sample-title {
  font-size: 13px;
  font-weight: 700;
  color: #F4F4F5;
}

.sample-subtitle {
  font-size: 11px;
  color: #A1A1AA;
}

.sample-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sample-card {
  text-align: left;
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid #2F2F35;
  background: #232328;
  color: #E4E4E7;
  cursor: pointer;
  transition: all 0.2s;
}

.sample-card:hover {
  border-color: #52525B;
  background: #2A2A2F;
}

.sample-card.primary {
  border-color: rgba(96, 165, 250, 0.5);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(37, 99, 235, 0.06));
}

.sample-name {
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
}

.sample-desc {
  font-size: 11px;
  color: #A1A1AA;
  margin-top: 4px;
}

.sample-cta {
  font-size: 11px;
  color: #93C5FD;
  margin-top: 6px;
  font-weight: 600;
}

.role-select {
  margin-top: 12px;
  background: #1F1F22;
  border: 1px solid #2A2A2E;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-select-title {
  font-size: 12px;
  color: #A1A1AA;
  font-weight: 600;
}

.role-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-option {
  text-align: left;
  background: #232326;
  border: 1px solid #2F2F35;
  border-radius: 8px;
  padding: 8px 10px;
  color: #E4E4E7;
  cursor: pointer;
  transition: all 0.2s;
}

.role-option:hover {
  border-color: #52525B;
  background: #2A2A2E;
}

.role-option.active {
  border-color: #60A5FA;
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.35);
}

.role-name {
  font-size: 13px;
  font-weight: 700;
  color: #F4F4F5;
}

.role-summary {
  font-size: 11px;
  color: #A1A1AA;
  margin-top: 4px;
}

.file-name {
  font-size: 13px;
  color: #fff;
  font-weight: 600;
}

.btn {
  height: 40px;
  border-radius: 8px;
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn.full { width: 100%; }

.btn.primary {
  background: #fff;
  color: #000;
}

.btn.primary:hover {
  background: #E4E4E7;
}

.btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.ghost {
  background: transparent;
  border: 1px solid #3F3F46;
  color: #A1A1AA;
}

.btn.ghost:hover {
  border-color: #71717A;
  color: #fff;
}

/* Spinner */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0,0,0,0.1);
  border-left-color: #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Tabs Control */
.tabs-control {
  display: flex;
  gap: 4px;
  background: #27272A;
  padding: 3px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  height: 28px;
  background: transparent;
  border: none;
  color: #A1A1AA;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
}

.tab-btn.active {
  background: #3F3F46;
  color: #fff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.badge-count {
  background: #EF4444;
  color: #fff;
  font-size: 10px;
  padding: 0 5px;
  border-radius: 10px;
  margin-left: 4px;
}

/* Lists */
.list-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.company-card, .app-card {
  background: #202023;
  border: 1px solid #27272A;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
}

.app-card {
  cursor: pointer;
  position: relative;
  pointer-events: auto;
  z-index: 1;
}

.app-card:hover {
  background: #27272A;
  transform: translateY(-1px);
}

.app-card.selected {
  border-color: #52525B;
  background: #2A2A2D;
}

.company-logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  flex-shrink: 0;
}

.company-logo.small {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.company-info, .app-info {
  flex: 1;
  min-width: 0;
}

.company-name, .app-company-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
}

.company-meta, .app-contact {
  font-size: 11px;
  color: #71717A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-tag {
  background: #3F3F46;
  color: #E4E4E7;
  padding: 1px 4px;
  border-radius: 4px;
  margin-right: 6px;
  font-size: 10px;
}

.btn-apply {
  background: #fff;
  color: #000;
  border: none;
  font-size: 11px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-apply.applied {
  background: #27272A;
  color: #71717A;
}

.app-header {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.app-status-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.status-applied { background: #27272A; color: #A1A1AA; }
.status-interview { background: rgba(245, 158, 11, 0.2); color: #FBBF24; }
.status-offer { background: rgba(16, 185, 129, 0.2); color: #34D399; }
.status-rejected { background: rgba(239, 68, 68, 0.2); color: #F87171; }

/* Main View Tabs */
.view-tabs {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: #18181B;
  border: 1px solid #27272A;
  border-radius: 100px;
  padding: 4px;
  display: flex;
  gap: 4px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.view-tab {
  height: 32px;
  padding: 0 16px;
  border-radius: 100px;
  background: transparent;
  border: none;
  color: #A1A1AA;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.view-tab.active {
  background: #fff;
  color: #000;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #EF4444;
  border-radius: 50%;
  position: absolute;
  top: 6px;
  right: 6px;
}

/* View Content */
.view-content {
  flex: 1;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.preview-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 80px 40px;
  display: flex;
  justify-content: center;
}

/* Chat UI */
.chat-mode {
  background: #09090B;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  background: #101012;
  border-left: 1px solid #1F1F22;
  border-right: 1px solid #1F1F22;
}

.chat-header {
  height: 64px;
  border-bottom: 1px solid #1F1F22;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  background: rgba(16, 16, 18, 0.8);
  backdrop-filter: blur(10px);
}

.chat-avatar-wrap {
  position: relative;
}

.company-logo.medium {
  width: 40px;
  height: 40px;
  font-size: 18px;
}

.online-dot {
  width: 10px;
  height: 10px;
  background: #10B981;
  border: 2px solid #101012;
  border-radius: 50%;
  position: absolute;
  bottom: 0;
  right: 0;
}

.chat-header-info {
  display: flex;
  flex-direction: column;
}

.chat-name {
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}

.chat-status {
  color: #71717A;
  font-size: 11px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Message Transitions */
.message-anim-enter-active,
.message-anim-leave-active {
  transition: all 0.3s ease;
}

.message-anim-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-anim-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Chat Message Styles */
.message-group {
  display: flex;
  gap: 12px;
  max-width: 80%;
  position: relative;
}

.message-meta {
  display: flex;
  gap: 6px;
  font-size: 10px;
  color: #52525B;
  margin-top: 4px;
  justify-content: flex-end; /* Align time to right for user */
}

.message-read {
  color: #10B981;
}

.message-group.assistant .message-meta {
  justify-content: flex-start;
}

.message-time {
  /* Removed absolute positioning */
}

/* Print Styles */
@media print {
  .sidebar, .tabs-control, .view-tabs, .chat-mode, .header-bar, .empty-main, .empty-state, .app-card, .company-card, .btn-apply, .btn-send, .chat-input-area, .chat-header, .chat-job-card, .toast-container {
    display: none !important;
  }
  
  .layout-container {
    display: block !important;
    height: auto !important;
    overflow: visible !important;
  }

  .main-view {
    padding: 0 !important;
    margin: 0 !important;
    height: auto !important;
    overflow: visible !important;
    width: 100% !important;
    position: static !important;
  }

  .view-content {
    padding: 0 !important;
    margin: 0 !important;
    height: auto !important;
    overflow: visible !important;
    width: 100% !important;
    position: static !important;
  }
  
  .preview-scroll {
    padding: 0 !important;
    height: auto !important;
    overflow: visible !important;
    display: block !important;
  }
  
  /* Reset resume page styles for print */
  .resume-page {
    box-shadow: none !important;
    margin: 0 !important;
    padding: 40px !important; /* Keep some padding */
    width: 100% !important;
    max-width: none !important;
    min-height: auto !important;
    transform: none !important;
    border: none !important;
  }
  
  /* Hide background */
  body, html {
    background: #fff !important;
    color: #000 !important;
    height: auto !important;
    overflow: visible !important;
  }

  /* Ensure resume content is visible */
  .resume-container {
    background: #fff !important;
    padding: 0 !important;
    display: block !important;
  }
}

.message-group.assistant {
  align-self: flex-start;
}

.message-group.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.company-logo.xs {
  width: 32px;
  height: 32px;
  font-size: 12px;
  border-radius: 8px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #3F3F46;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #fff;
  font-weight: 700;
}

.message-group .message-content {
  display: flex;
  flex-direction: column;
}

.message-group.assistant .message-content {
  align-items: flex-start;
}

.message-group.user .message-content {
  align-items: flex-end;
}

.bubble {
  padding: 12px 16px;
  border-radius: 12px;
  max-width: 100%;
  word-wrap: break-word;
  line-height: 1.5;
  font-size: 14px;
}

.assistant .bubble {
  background: #27272A;
  color: #E4E4E7;
  border-top-left-radius: 2px;
}

.user .bubble {
  background: #2563EB; /* Blue */
  color: #fff;
  border-top-right-radius: 2px;
}

.message-time {
  font-size: 10px;
  color: #52525B;
  align-self: flex-start;
}

.user .message-time {
  align-self: flex-end;
}

.typing-indicator {
  padding: 12px 20px;
  background: #27272A;
  border-radius: 12px;
  align-self: flex-start;
  margin-left: 44px;
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #71717A;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  border-top: 1px solid #1F1F22;
  display: flex;
  flex-direction: column;
}

.chat-tools {
  padding: 8px 16px;
  display: flex;
  gap: 8px;
  background: #101012;
}

.tool-btn {
  background: #27272A;
  border: none;
  border-radius: 100px;
  padding: 6px 12px;
  color: #A1A1AA;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #3F3F46;
  color: #fff;
}

.chat-input-row {
  display: flex;
  gap: 12px;
  padding: 16px;
  padding-top: 4px;
}

/* Job Card */
.chat-job-card {
  background: rgba(24, 24, 27, 0.5);
  backdrop-filter: blur(10px);
  padding: 12px 20px;
  border-bottom: 1px solid #1F1F22;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 10;
}

.job-card-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-card-title {
  color: #fff;
  font-weight: 700;
  font-size: 15px;
}

.job-card-salary {
  color: #10B981;
  font-weight: 700;
  font-size: 14px;
}

.job-card-sub {
  color: #71717A;
  font-size: 12px;
}

.chat-inp {
  flex: 1;
  height: 44px;
  background: #18181B;
  border: 1px solid #27272A;
  border-radius: 22px;
  padding: 0 20px;
  color: #fff;
  outline: none;
  font-size: 14px;
}

.chat-inp:focus {
  border-color: #52525B;
}

.btn-send {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.1s;
}

.btn-send:active {
  transform: scale(0.95);
}

.btn-send:disabled {
  background: #27272A;
  color: #52525B;
  cursor: default;
}

.send-icon {
  font-size: 18px;
  color: #000;
  margin-left: -2px;
  margin-top: 2px;
}

/* Empty States */
.empty-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #52525B;
}

.empty-main {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #52525B;
}

.empty-illustration, .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 8px;
}

.empty-desc, .empty-text {
  font-size: 14px;
}

@media print {
  .nav, .sidebar, .view-tabs, .chat-mode { display: none !important; }
  .page { background: #fff; height: auto; display: block; overflow: visible; }
  .content { display: block; overflow: visible; }
  .main-view { background: #fff; display: block; }
  .view-content { display: block; overflow: visible; }
  .preview-scroll { padding: 0; overflow: visible; height: auto; display: block; }
}

/* Enhanced Visuals */
.logo-icon {
  display: inline-block;
  animation: float 3s ease-in-out infinite;
  margin-right: 6px;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* Glitch Button Effect */
.glitch-effect {
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.glitch-effect::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: rotate(45deg) translateY(-100%);
  transition: transform 0.6s;
}

.glitch-effect:hover::after {
  transform: rotate(45deg) translateY(100%);
}

.glitch-effect:active {
  transform: scale(0.98);
}

/* Sample Card Enhanced */
.sample-card {
  position: relative;
  overflow: hidden;
  border: 1px solid #3F3F46;
  padding: 0;
  height: 80px;
}

.sample-bg-effect {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(120deg, rgba(37,99,235,0.1), transparent);
  opacity: 0.5;
  transition: all 0.5s;
}

.sample-card:hover .sample-bg-effect {
  background: linear-gradient(120deg, rgba(37,99,235,0.2), rgba(147,197,253,0.1));
}

.sample-content {
  position: relative;
  z-index: 2;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.sample-cta {
  color: #60A5FA;
  font-size: 11px;
  font-weight: 700;
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Upload Box Enhanced */
.upload-box {
  flex-direction: column;
  height: auto;
  min-height: 100px;
  padding: 24px 12px;
  background: #18181B;
  border: 2px dashed #3F3F46;
  justify-content: center;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.upload-sub {
  font-size: 10px;
  color: #52525B;
  margin-top: 2px;
}

.file-status {
  font-size: 10px;
  color: #10B981;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 8px;
  border-radius: 100px;
  margin-top: 4px;
  font-weight: 600;
}

/* Chat Header Enhanced */
.chat-header {
  justify-content: space-between;
}

.chat-header-info {
  flex: 1;
  margin-left: 12px;
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #10B981;
  font-weight: 500;
}

.status-indicator {
  font-size: 8px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}

.chat-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-btn {
  background: transparent;
  border: none;
  color: #A1A1AA;
  font-size: 16px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: #27272A;
  color: #fff;
}
</style>
