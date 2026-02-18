<template>
  <div class="resume-container">
    <div class="resume-page" v-if="resume">
      <header class="header">
        <div class="header-main">
          <div class="name">{{ resume.basics?.name || '未命名候选人' }}</div>
          <div class="title">{{ resume.basics?.title || '' }}</div>
        </div>
        <div class="contact">
          <div class="contact-item" v-if="resume.basics?.phone">
            <span class="icon">📱</span>{{ resume.basics.phone }}
          </div>
          <div class="contact-item" v-if="resume.basics?.email">
            <span class="icon">📧</span>{{ resume.basics.email }}
          </div>
          <div class="contact-item" v-if="resume.basics?.location">
            <span class="icon">📍</span>{{ resume.basics.location }}
          </div>
          <div class="contact-item" v-if="resume.basics?.website">
            <span class="icon">🔗</span>{{ resume.basics.website }}
          </div>
        </div>
      </header>

      <div class="content-body">
        <section class="section" v-if="resume.summary">
          <div class="section-title">
            <span class="section-icon">📝</span>个人简介
          </div>
          <div class="p summary-text">{{ resume.summary || '' }}</div>
        </section>

        <section class="section" v-if="resume.skills && resume.skills.length">
          <div class="section-title">
            <span class="section-icon">🛠️</span>技能专长
          </div>
          <div class="skills-grid">
            <div class="skill-group" v-for="(s, idx) in (resume.skills || [])" :key="idx">
              <div class="skill-category">{{ s.category }}</div>
              <div class="skill-items">
                <span class="skill-tag" v-for="(item, i) in (s.items || []).filter(Boolean)" :key="i">{{ item }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="section" v-if="resume.experience && resume.experience.length">
          <div class="section-title">
            <span class="section-icon">💼</span>工作经历
          </div>
          <div class="timeline">
            <div class="timeline-item" v-for="(e, idx) in (resume.experience || [])" :key="idx">
              <div class="timeline-header">
                <div class="company-info">
                  <span class="company-name">{{ e.company }}</span>
                  <span class="divider" v-if="e.location">|</span>
                  <span class="location" v-if="e.location">{{ e.location }}</span>
                </div>
                <div class="period">{{ e.start }} — {{ e.end }}</div>
              </div>
              <div class="role-title">{{ e.role }}</div>
              <ul class="bullets">
                <li v-for="(h, j) in (e.highlights || [])" :key="j">{{ h }}</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="section" v-if="resume.projects && resume.projects.length">
          <div class="section-title">
            <span class="section-icon">🚀</span>项目经验
          </div>
          <div class="timeline">
            <div class="timeline-item" v-for="(p, idx) in (resume.projects || [])" :key="idx">
              <div class="timeline-header">
                <div class="company-info">
                  <span class="project-name">{{ p.name }}</span>
                  <span class="divider" v-if="p.role">|</span>
                  <span class="project-role" v-if="p.role">{{ p.role }}</span>
                </div>
                <div class="period">{{ p.start }} — {{ p.end }}</div>
              </div>
              <ul class="bullets">
                <li v-for="(h, j) in (p.highlights || [])" :key="j">{{ h }}</li>
              </ul>
              <div class="tags-row" v-if="(p.tech || []).some(Boolean)">
                <span class="tag-label">技术栈:</span>
                <span class="tech-tag" v-for="(t, k) in (p.tech || []).filter(Boolean)" :key="k">{{ t }}</span>
              </div>
              <div class="tags-row" v-if="(p.metrics || []).some(Boolean)">
                <span class="tag-label">核心指标:</span>
                <span class="metric-tag" v-for="(m, k) in (p.metrics || []).filter(Boolean)" :key="k">{{ m }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="section" v-if="resume.education && resume.education.length">
          <div class="section-title">
            <span class="section-icon">🎓</span>教育背景
          </div>
          <div class="timeline">
            <div class="timeline-item" v-for="(ed, idx) in (resume.education || [])" :key="idx">
              <div class="timeline-header">
                <div class="company-info">
                  <span class="school-name">{{ ed.school }}</span>
                  <span class="divider" v-if="ed.degree">|</span>
                  <span class="degree" v-if="ed.degree">{{ ed.degree }}</span>
                  <span class="divider" v-if="ed.major">|</span>
                  <span class="major" v-if="ed.major">{{ ed.major }}</span>
                </div>
                <div class="period">{{ ed.start }} — {{ ed.end }}</div>
              </div>
              <ul class="bullets" v-if="(ed.highlights || []).length">
                <li v-for="(h, j) in (ed.highlights || [])" :key="j">{{ h }}</li>
              </ul>
            </div>
          </div>
        </section>

        <div class="grid-2-col">
          <section class="section" v-if="(resume.certs || []).length">
            <div class="section-title small">
              <span class="section-icon">📜</span>证书
            </div>
            <ul class="simple-list">
              <li v-for="(c, idx) in (resume.certs || [])" :key="idx">{{ c }}</li>
            </ul>
          </section>

          <section class="section" v-if="(resume.awards || []).length">
            <div class="section-title small">
              <span class="section-icon">🏆</span>奖项
            </div>
            <ul class="simple-list">
              <li v-for="(a, idx) in (resume.awards || [])" :key="idx">{{ a }}</li>
            </ul>
          </section>
        </div>

        <section class="section" v-if="(resume.portfolio || []).length">
          <div class="section-title">
            <span class="section-icon">🎨</span>作品集
          </div>
          <div class="portfolio-grid">
            <div class="portfolio-item" v-for="(w, idx) in (resume.portfolio || [])" :key="idx">
              <div class="portfolio-header">
                <span class="portfolio-name">{{ w.name }}</span>
                <a v-if="w.url" :href="w.url" target="_blank" class="portfolio-link">{{ w.url }}</a>
              </div>
              <div class="portfolio-desc">{{ w.desc }}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  resume: { type: Object, default: null }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Roboto:wght@400;500;700&display=swap');

.resume-container {
  padding: 20px;
  background: #525659;
  display: flex;
  justify-content: center;
}

.resume-page {
  width: 210mm; /* A4 width */
  min-height: 297mm; /* A4 height */
  background: #fff;
  color: #333;
  padding: 40px 50px;
  box-shadow: 0 0 20px rgba(0,0,0,0.3);
  font-family: 'Roboto', 'Noto Serif SC', sans-serif;
  line-height: 1.6;
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden; /* Prevent horizontal spill */
  word-wrap: break-word; /* Break long words */
  overflow-wrap: break-word;
}

/* Paper texture effect */
.resume-page::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
}

.header, .content-body {
  position: relative;
  z-index: 1;
}

.header {
  border-bottom: 2px solid #2c3e50;
  padding-bottom: 20px;
  margin-bottom: 25px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-main {
  flex: 1;
}

.name {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.title {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}

.contact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #555;
  align-items: flex-end;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon {
  font-size: 14px;
  opacity: 0.8;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-title.small {
  font-size: 15px;
  border-bottom: none;
  background: #f5f7fa;
  padding: 6px 10px;
  border-radius: 4px;
}

.section-icon {
  font-size: 16px;
}

.p {
  font-size: 14px;
  color: #444;
  white-space: pre-wrap;
  text-align: justify;
}

/* Skills */
.skills-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.skill-group {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.skill-category {
  font-size: 13px;
  font-weight: 700;
  color: #2c3e50;
  width: 80px;
  flex-shrink: 0;
  text-align: right;
}

.skill-items {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  font-size: 12px;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 4px;
  color: #333;
}

/* Timeline (Exp & Projects) */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-item {
  position: relative;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}

.company-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.company-name, .project-name, .school-name {
  font-size: 15px;
  font-weight: 700;
  color: #000;
}

.divider {
  color: #ccc;
  font-size: 12px;
}

.location, .project-role, .degree, .major {
  font-size: 14px;
  color: #555;
}

.period {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  font-family: 'Roboto', sans-serif;
}

.role-title {
  font-size: 14px;
  font-weight: 700;
  color: #444;
  margin-bottom: 6px;
}

.bullets {
  margin: 6px 0 0 18px;
  padding: 0;
  font-size: 13.5px;
  color: #333;
}

.bullets li {
  margin-bottom: 4px;
}

/* Tags Row */
.tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  flex-wrap: wrap;
}

.tag-label {
  font-weight: 700;
  color: #555;
}

.tech-tag {
  color: #2980b9;
  background: rgba(41, 128, 185, 0.1);
  padding: 1px 6px;
  border-radius: 3px;
}

.metric-tag {
  color: #27ae60;
  background: rgba(39, 174, 96, 0.1);
  padding: 1px 6px;
  border-radius: 3px;
}

/* Grid Layout */
.grid-2-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 24px;
}

.simple-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13.5px;
}

.simple-list li {
  padding: 4px 0;
  border-bottom: 1px dashed #eee;
}

.simple-list li:last-child {
  border-bottom: none;
}

/* Portfolio */
.portfolio-grid {
  display: grid;
  gap: 12px;
}

.portfolio-item {
  background: #f9f9f9;
  padding: 10px 14px;
  border-radius: 6px;
  border: 1px solid #eee;
}

.portfolio-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.portfolio-name {
  font-weight: 700;
  font-size: 14px;
}

.portfolio-link {
  font-size: 12px;
  color: #2980b9;
  text-decoration: none;
}

.portfolio-desc {
  font-size: 13px;
  color: #555;
}

@media print {
  .resume-container {
    padding: 0;
    background: none;
    display: block;
  }
  .resume-page {
    width: 100%;
    min-height: auto;
    box-shadow: none;
    margin: 0;
    padding: 20px 0; /* Adjust for print margins */
  }
}
</style>

